#! /usr/bin/env pypy3

import multiprocessing, logging
import json, random, time, math, base64
from http.client import HTTPSConnection, HTTPConnection
import argparse

parser = argparse.ArgumentParser(description='Start threads to doc.query repeately.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-t', dest='THREADS', type=int, default=1)
parser.add_argument('-b', dest='BATCHES', type=int, default=6)
parser.add_argument('ACTION', default='query', choices={'query', 'download', 'ping', 'benchmark'})
parser.add_argument('--batch_size', dest='BATCH_SIZE', type=int, default=100)
parser.add_argument('-v', action='count', default=0)
parser.add_argument('-r', dest='REPORT', type=int, default=0)
ARGS = parser.parse_args()
#TODO support batch for both seconds and iterations

multiprocessing.current_process().name = "M"
if ARGS.v>0:
    lvl=logging.DEBUG
else:
    lvl=logging.INFO
logging.basicConfig(format=' [%(asctime)s.%(msecs)03d@%(processName)s] %(message)s', datefmt='%H:%M:%S', level=lvl)
logging.info(ARGS)

class TestClient(multiprocessing.Process):
    def __init__(self, name, host, port, counter, IS_EXIT):
        multiprocessing.Process.__init__(self, name=name)
        self.host = host
        self.port = port
        self.counter = counter
        self.IS_EXIT = IS_EXIT
        self.conn = HTTPSConnection(self.host, self.port,
                timeout=ARGS.BATCH_SIZE*ARGS.BATCHES/2)
        self.ids = list(TestClient.ids)
        print(self.ids[0])
        if ARGS.v>1:
            #self.conn.set_debuglevel(1)
            HTTPConnection.debuglevel=1

    def close(self):
        logging.info("EXIT.")
        self.conn.close()

    def parse_response(self):
        resp = self.conn.getresponse()
        result = json.loads(resp.read().decode('utf-8'))
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("--> %s" % json.dumps(result, indent=2))
        if (resp.status != 200):
            logging.error("%d: %d (%s): %s" % (self.counter.value, 
                        resp.status, resp.reason, result['message']))
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

    def ping(self, is_print):
        self.conn.request("GET", "/")
        resp = self.conn.getresponse()
        read = resp.read()
        if (resp.status != 200):
            result = json.loads(read.decode('utf-8'))
            logging.error("%d: %d (%s): %s" % (self.counter.value,
                        resp.status, resp.reason, result['message']))
            return False
        if is_print:
            result = json.loads(read.decode('utf-8'))
            logging.info("/: %s" % json.dumps(result, indent=2))
        return True

    def benchmark(self, is_print):
        self.conn.request("GET", "/api?method=job.type.list&token=" + self.token)
        resp = self.conn.getresponse()
        read = resp.read()
        if (resp.status != 200):
            result = json.loads(read.decode('utf-8'))
            logging.error("%d: %d (%s): %s" % (self.counter.value,
                        resp.status, resp.reason, result['message']))
            return False
        if is_print:
            result = json.loads(read.decode('utf-8'))
            logging.info("job.type.list-> name : %s" % result["response"][0]["name"])
        return True

    def doc_query(self, merchantid, is_print):
        logging.debug("doc.query?")
        self.conn.request("POST", "/api?method=doc.query&token="+self.token,\
            '{"query":{"metadata.parameter.merchantid":"%s"}}' % merchantid,\
            {"Content-type":"application/json"})
        response = self.parse_response()
        if response==None:
            return False

        if ARGS.ACTION[0]=="d": #download
            id = response[0]["_id"]
            pdf = response[0]["filename"]
            if self.doc_download(id, pdf, is_print or self.counter.value==0) and is_print:
                logging.info("%d: %s => %s => %s" % (self.counter.value, merchantid, id, pdf))
        elif is_print:
            logging.info("%d: %s => %s" % (self.count, merchantid, " ".join([e['filename'] for e in response])))
        return True

    def doc_download(self, id, pdf, is_save):
        logging.debug("doc.download?")
        self.conn.request("GET", "/api?method=doc.download&id=%s&token=%s" % (id, self.token))
        response = self.parse_response()
        if response==None:
            return False

        if is_save:
            with open(pdf, 'wb') as f:
                f.write(base64.b64decode(bytes(response, 'utf-8')))
        return True

    def run(self):
        global ARGS
        if ARGS.ACTION == "ping":
            while not self.IS_EXIT.value:
                if self.ping(ARGS.REPORT>0 and self.counter.value%ARGS.REPORT==0):
                    self.counter.value += 1
            self.close()
            return

        if not self.user_authorize('system', 'manage'):
            return
        if ARGS.ACTION == "benchmark":
            while not self.IS_EXIT.value:
                if self.benchmark(ARGS.REPORT>0 and self.counter.value%ARGS.REPORT==0):
                    self.counter.value += 1
            self.close()
            return
        while True:
            for id in self.ids:
                if self.IS_EXIT.value:
                    self.close()
                    return
                logging.debug(id)
                if self.doc_query(id, 
                        ARGS.REPORT>0 and self.counter.value%ARGS.REPORT==0):
                    self.counter.value += 1

def get_merchantids(host, port, database, username, password):
    import os
    filename = "/TEST/data/key/u1000000d1.shuf"
    if os.access(filename, os.R_OK):
        with open(filename) as f:
            ids = [line.rstrip() for line in f]
            return ids

    from pymongo import MongoClient
    logging.info("Connect to mongo://{3}:{4}@{0}:{1}/{2} for merchantid.".format(
                host,port,database,username,password))
    mg = MongoClient(host, port)
    db = mg[database]
    db.authenticate(username, password)
    db = mg["kyddata"]
    files = db.fs.files
    ids = {row["metadata"]["parameter"]["merchantid"]
           for row in files.find(projection={"metadata.parameter.merchantid":1,"_id":0}, limit=1000001)}
    logging.info("Get %d merchantid." % len(ids))
    ids = list(ids);     #logging.info("Listed.")

    mg.close()
    return ids

################################## MAIN ###################################
TestClient.ids = get_merchantids('192.168.99.242', 40000, 'kydsystem', 'kyd', 'kyd')
IS_EXIT = multiprocessing.Value('i', 0, lock=False)

counters = list(range(ARGS.THREADS))
tc = list(range(ARGS.THREADS))
for i in range(ARGS.THREADS):
    random.shuffle(TestClient.ids)
    counters[i] = multiprocessing.Value('i', 0, lock=False)
    tc[i] = TestClient("%s" % (i+1), "192.168.99.242", 9091, counters[i], IS_EXIT)
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
        counts = [counters[i].value for i in range(ARGS.THREADS)]
        total = sum(counts)
        report_list.append(total-last_total)
        logging.info("+%d = %d (%s)" % (total-last_total, total,
                    "".join(map(lambda i: " +%d" % i, [a-b for a,b in zip(counts, last_counts)]))))

        last_counts = counts
        last_total = total
else:
    IS_EXIT.value = 1

for i in range(ARGS.THREADS):
    tc[i].join(10)

######################### Final Report ######################################
report_list = report_list[(len(report_list)-1)//3+1:]

if ARGS.ACTION == "benchmark":
    cmd = "job.type.list"
elif ARGS.ACTION == "ping":
    cmd = "ping"
elif ARGS.ACTION == "download":
    cmd = "doc.query&download"
else:
    cmd = "doc.query"
logging.info("%d thread(s): %.1f %s/second  <= (%s)/%d/%d" % 
        (ARGS.THREADS, sum(report_list)/len(report_list)/ARGS.BATCH_SIZE, cmd,
         "+".join(map(str, report_list)), len(report_list), ARGS.BATCH_SIZE))
