#! /usr/bin/env python3.4

import threading, logging
import json, random
import http.client
from pymongo import MongoClient
import argparse

parser = argparse.ArgumentParser(description='Start threads to doc.query repeately.')
parser.add_argument('-t', dest='THREADS', type=int, default=1)
parser.add_argument('-n', dest='NUM2RUN', type=int, default=1)
ARGS = parser.parse_args()

logging.basicConfig(format=' [%(asctime)s] %(message)s', datefmt='%H:%M:%S', 
        level=logging.INFO)

class TestClient(threading.Thread):
    host = None
    port = None
    conn = None
    token = None
    count = 0

    def __init__(self, host, port=None):
        threading.Thread.__init__(self, name=threading.active_count())
        self.host = host
        self.port = port
        self.conn = http.client.HTTPSConnection(self.host, self.port)
        #self.conn.set_debuglevel(1)

    def close(self):
        self.conn.close()

    def user_authorize(self, userid, password):
        self.conn.request("POST", "/api?method=user.authorize", \
            '{"userid":"%s","password":"%s"}' % (userid, password),\
            {"Content-type":"application/json"})
        resp = self.conn.getresponse()
        data = resp.read()
        if (resp.code != 200):
            logging.error("\b@%s  %d: %d %s" % (self.name, self.count,
                        resp.code, resp.reason))
            return

        dict = json.loads(data.decode())
        self.token = dict['response']['token']
        print(self.name, ":", self.token)

    def doc_query(self, merchantid, is_print):
        self.conn.request("POST", "/api?method=doc.query&token="+self.token,\
            '{"query":{"metadata.parameter.merchantid":"%s"}}' % merchantid,\
            {"Content-type":"application/json"})
        resp = self.conn.getresponse()
        data = resp.read()
        if (resp.code != 200):
            logging.error("\b@%s  %d: %d %s" % (self.name, self.count,
                        resp.code, resp.reason))
            return

        if (is_print):
            dict = json.loads(data.decode())
            #print(json.dumps(dict, indent=2))
            logging.info("\b@%s  %d: %s => %s" % (self.name, self.count, merchantid, 
                         " ".join([e['filename'] for e in dict['response']])))

    def run(self):
        global ARGS
        count = 0
        while (count != ARGS.NUM2RUN):
            self.user_authorize('system', 'manage')
            count += 1
#        while True:
#            global ids
#            for id in ids:
#                self.doc_query(id, self.count % 1000 == 0)
#                self.count+=1

def get_merchantids(host, port, database, username, password):
    logging.info("Connect to mongo://{3}:{4}@{0}:{1}/{2} for merchantid.".format(
                host,port,database,username,password))
    mg = MongoClient(host, port)
    db = mg[database]
    db.authenticate(username, password)
    files = db.fs.files
    ids = {row["metadata"]["parameter"]["merchantid"]
           for row in files.find(fields={"metadata.parameter.merchantid":1,"_id":0}, limit=10)}
    logging.info("Get %d merchantid." % len(ids))
    ids = list(ids);     logging.info("Listed.")
    random.shuffle(ids); logging.info("Shuffled.")

    mg.close()
    return ids

################################## MAIN ###################################
ids = get_merchantids('192.168.99.241', 40000, 'kydsystem', 'kyd', 'kyd')

for i in range(ARGS.THREADS):
    tc = TestClient("192.168.99.241", 9091)
    tc.start()
tc.join()
tc.close()

