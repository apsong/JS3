#! /usr/bin/env python3.4

import threading, logging, sys, pathlib
import json, random, time, math, base64
import http.client
from pymongo import MongoClient
import argparse
from queue import Queue

parser = None
PROGRAM=pathlib.PurePosixPath(sys.argv[0]).name
if PROGRAM == 'nmb.cp':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', action='store_true')
    parser.add_argument('SRC_FILE', nargs='+')
    parser.add_argument('DST_FILE', help='[host:[port:]]file')
    parser.add_argument('-v', action='count', default=0)
    parser.add_argument('--threads', '-t', type=int, default=1, help='Number of worker threads')
elif PROGRAM == 'nmb.rm':
    print('rm')
elif PROGRAM == 'nmb.mv':
    print('mv')
elif PROGRAM == 'nmb.ls':
    print('ls')

ARGS = parser.parse_args()

threading.current_thread().name = "M"
if ARGS.v>0:
    lvl=logging.DEBUG
else:
    lvl=logging.INFO
logging.basicConfig(format=' [%(asctime)s.%(msecs)03d@%(threadName)s] %(message)s', datefmt='%H:%M:%S', level=lvl)
logging.info(ARGS)

class TestClient(threading.Thread):
    ERRORS = list()
    def __init__(self, host, port, task_q):
        threading.Thread.__init__(self, name=threading.active_count())
        self.host = host
        self.port = port
        self.conn = http.client.HTTPSConnection(self.host, self.port, timeout=60)
        if ARGS.v>1:
            self.conn.set_debuglevel(1)
        self.task_q = task_q

    def close(self):
        logging.debug("close")
        self.conn.close()

    def user_authorize(self, userid, password):
        logging.info("TOKEN?")
        self.conn.request("POST", "/api?method=user.authorize", \
            '{"userid":"%s","password":"%s"}' % (userid, password),\
            {"Content-type":"application/json"})
        resp = self.conn.getresponse()
        data = resp.read()
        if (resp.code != 200):
            logging.error("%d %s" % (resp.code, resp.reason))
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
            logging.error("%d %s" % (resp.code, resp.reason))
            return False

        return True

    def run(self):
        if not self.user_authorize('system', 'manage'):
            return
        while True:
            task = self.task_q.get()
            logging.debug(task)

            if task[0] == 'UPLOAD':
                print(task[0])
            elif task[0] == 'DOWNLOAD':
                print(task[0])
            elif task[0] == 'LIST':
                print(task[0])
            elif task[0] == 'RENAME':
                print(task[0])
            elif task[0] == 'REMOVE':
                print(task[0])
            elif task[0] == 'EXIT':
                self.close()
                logging.debug("Exit.")
                self.task_q.task_done()
                return
            else:
                msg = "Invalid task: %s" % task
                logging.error(msg)
                TestClient.ERRORS.append(msg)

            self.task_q.task_done()
            time.sleep(1)

################################## MAIN ###################################
q = Queue()
for i in range(ARGS.threads):
    t = TestClient('192.168.99.242', '9091', q)
    #t.daemon = True
    t.start()
    #time.sleep(1)

q.put(['UPLOAD', 'local', 'remote'])
q.put(['UPLOAD', 'local', 'remote'])
q.put(['UPLOAD', 'local', 'remote'])
q.put(['UPLOAD', 'local', 'remote'])
q.put(['UPLOAD', 'local', 'remote'])
q.put(['DOWNLOAD', 'local', 'remote'])
q.put(['DOWNLOAD', 'local', 'remote'])
q.put(['DOWNLOAD', 'local', 'remote'])
q.put(['DOWNLOAD', 'local', 'remote'])
q.put(['DOWNLOAD', 'local', 'remote'])
q.put(['WHAT', 'local', 'remote'])
q.join()

############################# RESULT ##########################
print("======================= ERRORS: %d ======================" % len(TestClient.ERRORS))
for msg in TestClient.ERRORS:
    print(msg)
############################# CLEAN UP ##########################
for i in range(ARGS.threads):
    q.put(['EXIT'])
logging.debug("Finished.")
