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
parser.add_argument('-v', action='count', default=0)
parser.add_argument('-r', dest='REPORT', type=int, default=0)
ARGS = parser.parse_args()
#TODO support batch for both seconds and iterations

threading.current_thread().name = "M"
if ARGS.v>0:
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
        self.conn = http.client.HTTPSConnection(self.host, self.port,
                timeout=ARGS.BATCH_SIZE*ARGS.BATCHES/2)
        self.count = 0
        if ARGS.v>1:
            #self.conn.set_debuglevel(1)
            http.client.HTTPConnection.debuglevel=1

    def close(self):
        self.conn.close()

    def parse_response(self):
        resp = self.conn.getresponse()
        result = json.loads(resp.read().decode('utf-8'))
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("--> %s" % json.dumps(result, indent=2))
        if (resp.code != 200):
            logging.error("%d/%d: %d (%s): %s" % (self.count, TestClient.TOTAL_COUNT,
                        resp.code, resp.reason, result['message']))
            return None
        return result["response"]

    def user_authorize(self, userid, password):
        logging.info("TOKEN?")
        self.conn.request("POST", "/api?method=user.authorize", \
            '{"userid":"%s","password":"%s"}' % (userid, password),\
            {"Content-type":"application/json"})
        response = self.parse_response()
        self.token = response['token']
        logging.info("TOKEN: %s" % (self.token))
        return True

    def doc_query(self, merchantid, is_print):
        logging.debug("doc.query?")
        self.conn.request("POST", "/api?method=doc.query&token="+self.token,\
            '{"query":{"metadata.parameter.merchantid":"%s"}}' % merchantid,\
            {"Content-type":"application/json"})
        response = self.parse_response()
        if response==None:
            return False

        if ARGS.DOWNLOAD:
            id = response[0]["_id"]
            pdf = response[0]["filename"]
            if self.doc_download(id, pdf, is_print or TestClient.TOTAL_COUNT==0) and is_print:
                logging.info("%d: %s => %s => %s" % (TestClient.TOTAL_COUNT, merchantid, id, pdf))
        elif is_print:
            logging.info("%d: %s => %s" % (TestClient.TOTAL_COUNT, merchantid, " ".join([e['filename'] for e in response])))
        return True

    def doc_download(self, id, pdf, is_save):
        logging.debug("doc.download?")
        self.conn.request("GET", "/api?method=doc.download&id=%s&token=%s" % (id, self.token))
        response = self.parse_response()
        if response==None:
            return False

        if is_save:
            with open(pdf, 'wb') as f:
                f.write(base64.b64decode(response))
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
                logging.debug(id)
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
           for row in files.find(fields={"metadata.parameter.merchantid":1,"_id":0}, limit=1001)}
    logging.info("Get %d merchantid." % len(ids))
    ids = list(ids);     #logging.info("Listed.")
    random.shuffle(ids); #logging.info("Shuffled.")

    mg.close()
    return ids

################################## MAIN ###################################
ids = get_merchantids('192.168.99.242', 40000, 'kydsystem', 'kyd', 'kyd')

tc = list(range(ARGS.THREADS))
for i in range(ARGS.THREADS):
    tc[i] = TestClient("192.168.99.242", 9091)
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
