#! /usr/bin/env pypy3

import argparse
import multiprocessing, logging
import json, random, time, math, base64
from http.client import HTTPSConnection, HTTPConnection

parser = argparse.ArgumentParser(description='Start threads to doc.query repeately.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ACTION', default='query', choices={'query', 'download', 'ping', 'benchmark'})
parser.add_argument('-t', dest='THREADS', type=int, default=1)
parser.add_argument('-b', dest='BATCH_NUM', type=int, default=6)
parser.add_argument('-B', dest='BATCH_SECONDS', type=int, default=100)
parser.add_argument('--report', type=int, default=0)
parser.add_argument('--no_verify', action='store_true', default=False)
parser.add_argument('-v', action='count', default=0)
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
                timeout=ARGS.BATCH_SECONDS*ARGS.BATCH_NUM/2)
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
        logging.info("TOKEN: %s...%s" % (self.token[:16], self.token[-16:]))
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

    def doc_query(self, merchantid, expected_pdf, is_print):
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
            if self.doc_download(id, pdf, is_print) and is_print:
                logging.info("%d: %s => %s => %s" % (self.counter.value, merchantid, id, pdf))
        elif not ARGS.no_verify:
            if expected_pdf not in [e["filename"] for e in response]:
                logging.error("VERIFY FAILED: id: %s => expected %s, but got %s" %
                        (merchantid, expected_pdf, json.dumps(response, indent=2)))
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
                if self.ping(ARGS.report>0 and self.counter.value%ARGS.report==0):
                    self.counter.value += 1
            self.close()
            return

        if not self.user_authorize('system', 'manage'):
            return
        if ARGS.ACTION == "benchmark":
            while not self.IS_EXIT.value:
                if self.benchmark(ARGS.report>0 and self.counter.value%ARGS.report==0):
                    self.counter.value += 1
            self.close()
            return

        global IDS
        ids=IDS #TODO: gloabl variable affect performance?
        logging.info("[%s ... %s]" % (ids[0], ids[-1]))
        while True:
            for id, pdf in ids:
                if self.IS_EXIT.value:
                    self.close()
                    return
                logging.debug(id)
                if self.doc_query(id, pdf,
                        ARGS.report>0 and self.counter.value%ARGS.report==0):
                    self.counter.value += 1

def get_merchantids_from_db(host, port, database, username, password):
    from pymongo import MongoClient
    logging.info("Connect to mongo://{3}:{4}@{0}:{1}/{2} for merchantid.".format(
                host,port,database,username,password))
    mg = MongoClient(host, port)
    db = mg[database]
    db.authenticate(username, password)
    db = mg["kyddata"]
    files = db.fs.files
    ids = {row["metadata"]["parameter"]["merchantid"] : row["filename"]
        for row in files.find(projection={"metadata.parameter.merchantid":1,"filename":1,"_id":0}, limit=101)}
    ids = list(ids.items())
    random.shuffle(ids)
    logging.info("Get %d (merchantid,pdf): [%s ... %s]" % (len(ids), ids[0], ids[-1]))

    mg.close()
    return ids

def get_merchantids():
    import os, pickle
    keyfile = "./id_pdf.pickle"
    if os.access(keyfile, os.R_OK):
        with open(keyfile, 'rb') as f:
            #ids = [line.rstrip() for line in f]
            ids = pickle.load(f)
        logging.info("Load %d (merchantid,pdf) from %s" % (len(ids), keyfile))
    else:
        ids = get_merchantids_from_db('192.168.99.242', 40000, 'kydsystem', 'kyd', 'kyd')
        with open(keyfile, 'wb') as f:
            pickle.dump(ids, f)
        logging.info("Save (merchantid,pdf) into %s" % keyfile)
    return ids

################################## MAIN ###################################
if ARGS.ACTION in ['query', 'download']:
    IDS = get_merchantids()
IS_EXIT = multiprocessing.Value('i', 0, lock=False)

counters = list(range(ARGS.THREADS))
tc = list(range(ARGS.THREADS))
for i in range(ARGS.THREADS):
    counters[i] = multiprocessing.Value('i', 0, lock=False)
    tc[i] = TestClient("%s" % (i+1), "192.168.99.242", 9091, counters[i], IS_EXIT)
    tc[i].start()
    random.shuffle(IDS)

last_counts = [0] * ARGS.THREADS
last_total  = 0
report_list = list()
next = time.time()
end  = time.time() + ARGS.BATCH_SECONDS * ARGS.BATCH_NUM
while (time.time() < end):
    time.sleep(1)
    if (time.time() >= next):
        next += ARGS.BATCH_SECONDS
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
        (ARGS.THREADS, sum(report_list)/len(report_list)/ARGS.BATCH_SECONDS, cmd,
         "+".join(map(str, report_list)), len(report_list), ARGS.BATCH_SECONDS))
