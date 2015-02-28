#! /usr/bin/env python3.4

import threading, logging
import json, random, time, math, base64
import http.client
from pymongo import MongoClient
import argparse

parser = argparse.ArgumentParser(description='Start threads to doc.query repeately.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-t', dest='THREADS', type=int, default=1)
parser.add_argument('-b', dest='BATCHES', type=int, default=6)
parser.add_argument('--download', dest='DOWNLOAD', action='store_true')
parser.add_argument('--batch_size', dest='BATCH_SIZE', type=int, default=100)
parser.add_argument('--debug', dest='DEBUG', action='store_true')
parser.add_argument('-r', dest='REPORT', type=int, default=0)
ARGS = parser.parse_args()
#TODO support batch for both seconds and iterations

threading.Thread.name = "M"
if ARGS.DEBUG:
    lvl=logging.DEBUG
else:
    lvl=logging.INFO
logging.basicConfig(format=' [%(asctime)s.%(msecs)03d@%(threadName)s] %(message)s', datefmt='%H:%M:%S', level=lvl)
logging.info(ARGS)

class TestClient(threading.Thread):
    TOTAL_COUNT = 0
    IS_EXIT = False

    def __init__(self, host, port=None):
        threading.Thread.__init__(self, name=threading.active_count())
        self.host = host
        self.port = port
        self.conn = http.client.HTTPSConnection(self.host, self.port)
        self.count = 0
        #self.conn.set_debuglevel(1)

    def close(self):
        self.conn.close()

    def user_authorize(self, userid, password):
        logging.info("TOKEN?")
        self.conn.request("POST", "/api?method=user.authorize", \
            '{"userid":"%s","password":"%s"}' % (userid, password),\
            {"Content-type":"application/json"})
        resp = self.conn.getresponse()
        data = resp.read()
        if (resp.code != 200):
            logging.error("%d/%d: %d %s" % (self.count, TestClient.TOTAL_COUNT, resp.code, resp.reason))
            return False

        dict = json.loads(data.decode())
        self.token = dict['response']['token']
        logging.info("TOKEN: %s" % (self.token))
        return True

    def doc_query(self, merchantid, is_print):
        logging.debug("doc.query?")
        self.conn.request("POST", "/api?method=doc.query&token="+self.token,\
            '{"query":{"metadata.parameter.merchantid":"%s"}}' % merchantid,\
            {"Content-type":"application/json"})
        resp = self.conn.getresponse()
        logging.debug("doc.query.response!")
        data = resp.read()
        if (resp.code != 200):
            logging.error("%d/%d: %d %s" % (self.count, TestClient.TOTAL_COUNT, resp.code, resp.reason))
            return False

        if ARGS.DOWNLOAD:
            dict = json.loads(data.decode())
            #print(json.dumps(dict, indent=2))
            #for e in dict['response']:
            id = dict['response'][0]["_id"]
            pdf = dict['response'][0]["filename"]
            if self.doc_download(id, pdf, is_print) and is_print:
                logging.info("%d: %s => %s => %s" % (TestClient.TOTAL_COUNT, merchantid, id, pdf))
        elif is_print:
            dict = json.loads(data.decode())
            #print(json.dumps(dict, indent=2))
            logging.info("%d: %s => %s" % (TestClient.TOTAL_COUNT, merchantid, " ".join([e['filename'] for e in dict['response']])))
        return True

    def doc_download(self, id, pdf, is_save):
        logging.debug("doc.download?")
        self.conn.request("GET", "/api?method=doc.download&id=%s&token=%s" %
                (id, self.token))
        resp = self.conn.getresponse()
        logging.debug("doc.download.response!")
        data = resp.read()
        if (resp.code != 200):
            logging.error("%d/%d: %d %s" % (self.count, TestClient.TOTAL_COUNT, resp.code, resp.reason))
            return False

        if is_save:
            dict = json.loads(data.decode())
            #print(json.dumps(dict, indent=2))
            with open(pdf, 'wb') as f:
                f.write(base64.b64decode(dict['response']))
        return True

    def run(self):
        global ARGS, ids
        if not self.user_authorize('system', 'manage'):
            return
        while True:
            for id in ids:
                if (TestClient.IS_EXIT):
                    logging.info("Exit")
                    return
                if self.doc_query(id, 
                        ARGS.REPORT>0 and TestClient.TOTAL_COUNT%ARGS.REPORT==0):
                    self.count += 1
                    TestClient.TOTAL_COUNT += 1

def get_merchantids(host, port, database, username, password):
    logging.info("Connect to mongo://{3}:{4}@{0}:{1}/{2} for merchantid.".format(
                host,port,database,username,password))
    mg = MongoClient(host, port)
    db = mg[database]
    db.authenticate(username, password)
    db = mg["kyddata"]
    files = db.fs.files
    ids = {row["metadata"]["parameter"]["merchantid"]
           for row in files.find(fields={"metadata.parameter.merchantid":1,"_id":0}, limit=10001)}
    logging.info("Get %d merchantid." % len(ids))
    ids = list(ids);     #logging.info("Listed.")
    random.shuffle(ids); #logging.info("Shuffled.")

    mg.close()
    return ids

################################## MAIN ###################################
ids = get_merchantids('192.168.99.85', 40000, 'kydsystem', 'kyd', 'kyd')

tc = list(range(ARGS.THREADS))
for i in range(ARGS.THREADS):
    tc[i] = TestClient("192.168.99.85", 9091)
    time.sleep(1)
    tc[i].start()

last_counts = [0] * ARGS.THREADS
last_total  = 0
report_list = list()
next = time.time()
end  = time.time() + ARGS.BATCH_SIZE * ARGS.BATCHES
while (time.time() < end):
    time.sleep(1)
    if (time.time() >= next):
        next += ARGS.BATCH_SIZE
        counts = [tc[i].count for i in range(ARGS.THREADS)]
        report_list.append(TestClient.TOTAL_COUNT-last_total)
        logging.info("+%d = %d (%s)" % (TestClient.TOTAL_COUNT-last_total,
                    TestClient.TOTAL_COUNT,
                    "".join(map(lambda i: " +%d" % i, [a-b for a,b in zip(counts, last_counts)]))))

        last_counts = counts
        last_total = TestClient.TOTAL_COUNT
else:
    TestClient.IS_EXIT = True

for i in range(ARGS.THREADS):
    tc[i].join()
for i in range(ARGS.THREADS):
    tc[i].close()

######################### Final Report ######################################
report_list = report_list[(len(report_list)-1)//3+1:]

if ARGS.DOWNLOAD:
    d = "&download"
else:
    d= ""
logging.info("%d thread(s): %.1f doc.query%s/second  <= (%s)/%d/%d" % 
        (ARGS.THREADS, sum(report_list)/len(report_list)/ARGS.BATCH_SIZE, d,
         "+".join(map(str, report_list)), len(report_list), ARGS.BATCH_SIZE))
