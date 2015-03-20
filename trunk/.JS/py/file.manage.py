#! /usr/bin/env python3.4

import sys, os
from pathlib import PosixPath
import logging, argparse
import threading, time
import json, base64
import http.client
from queue import Queue

class TestClient(threading.Thread):
    ERRORS = list()
    def __init__(self, host, port, task_q):
        threading.Thread.__init__(self, name=threading.active_count())
        self.host = host
        self.port = port
        self.conn = http.client.HTTPSConnection(self.host, self.port, timeout=60)
        self.conn.connect()
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
        self.token = TestClient._parse_response(self.conn)['token']
        logging.info("TOKEN: %s" % (self.token))
        return True

    def _parse_response(conn):
        resp = conn.getresponse()
        result = json.loads(str(resp.read(), 'utf-8'))
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("--> %s" % json.dumps(result, indent=2))
        if (resp.code != 200):
            logging.error("%d (%s): %s" % (resp.code, resp.reason, result['message']))
            return None
        return result["response"]

    def _check_response(conn):
        resp = conn.getresponse()
        read = resp.read()
        logging.debug(read)
        if (resp.code != 200 or logging.getLogger().isEnabledFor(logging.DEBUG)):
            result = json.loads(str(read, 'utf-8'))
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug("--> %s" % json.dumps(result, indent=2))
            if resp.code != 200:
                logging.error("%d (%s): %s" % (resp.code, resp.reason, result['message']))
                return False
        return True

    def do_mkdir(self, dir_name, remote_dir):
        logging.debug("file.add dir?")
        self.conn.request("POST", "/api?method=file.add&token="+self.token,\
            '{"fileName":"%s", "filePath":"%s", "fileType":"1", "owner":"*"}' % (dir_name, remote_dir),\
            {"Content-type":"application/json"})
        return TestClient._check_response(self.conn)

    def do_upload(self, local_file, remote_dir):
        logging.debug("file.add file?")
        self.conn.request("POST", "/api?method=file.add&token="+self.token,\
            '{"fileName":"%s", "filePath":"%s", "fileType":"0", "owner":"*"}' % (local_file, remote_dir),\
            {"Content-type":"application/json"})
        return TestClient._check_response(self.conn)

    def do_download(self, remote_file, local_dir):
        logging.debug("file.download?")
        self.conn.request("POST", "/api?method=file.download&token="+self.token,\
            '{"path":"%s"}' % remote_file,\
            {"Content-type":"application/json"})
        R = TestClient._parse_response(self.conn)
        local_file = os.path.join(local_dir, os.path.basename(remote_file))
        with open(local_file, 'wb') as f:
            f.write(base64.b64decode(R))

    def do_delete(self, files):
        logging.debug("file.delete?")
        self.conn.request("POST", "/api?method=file.delete&token="+self.token,\
            '{"filePaths":["%s"]}' % '","'.join(files),\
            {"Content-type":"application/json"})
        return TestClient._check_response(self.conn)

    def do_rename(self, path, new_name):
        logging.debug("file.rename?")
        self.conn.request("POST", "/api?method=file.rename&token="+self.token,\
            '{"path":"%s", "newFileName":"%s"}' % (path, new_name),\
            {"Content-type":"application/json"})
        return TestClient._check_response(self.conn)

    def _desc_path(F):
        print("%3s %-30s %-40s %s" % (F["fileType"]==1 and "[d]" or "   ", F["path"], F["attributes"], F["lastModifiedTime"]))

    def _stat(self, path):
        logging.debug("file.query.path?")
        self.conn.request("POST", "/api?method=file.query.path&token="+self.token,\
            '{"path":"%s"}' % path,\
            {"Content-type":"application/json"})
        return TestClient._parse_response(self.conn)

    def _stat2(self, path):
        logging.debug("file.query?")
        self.conn.request("POST", "/api?method=file.query&token="+self.token,\
            '{"path":"%s"}' % path,\
            {"Content-type":"application/json"})
        return TestClient._parse_response(self.conn)

    def do_stat(self, path):
        R = self._stat(path)
        TestClient._desc_path(R)
        return R!=None

    def do_ls(self, path):
        R = self._stat2(path)
        for r in R:
            TestClient._desc_path(r)
        return R!=None

    def do_ls_r(self, path):
        R = self._stat2(path)
        for r in R:
            TestClient._desc_path(r)
            if r["fileType"]==1:
                self.do_ls_r(r["path"])
        return R!=None

    def run(self):
        if not self.user_authorize('system', 'manage'):
            return
        while True:
            task = self.task_q.get()
            logging.debug(task)

            if task[0] == 'UPLOAD':
                p = PosixPath(task[1])
                if p.is_dir():
                    target_dir = os.path.join(task[2], p.name)
                    if self.do_mkdir(p.name, task[2]):
                        for f in p.iterdir():
                            self.task_q.put(['UPLOAD', str(f), target_dir])
                else:
                    self.do_upload(str(p), task[2])

                print(task[0])
            elif task[0] == 'DOWNLOAD':
                R = self._stat(task[1])
                if R["fileType"]==1: #dir
                    p = PosixPath(task[2]).joinpath(R["name"]=="" and "ROOT" or R["name"])
                    p.mkdir()
                    target_dir = os.path.join(task[2], p.name)
                    for r in self._stat2(task[1]):
                        self.task_q.put(['DOWNLOAD', r["path"], target_dir])
                else:
                    self.do_download(task[1], task[2])
            elif task[0] == 'STAT':
                self.do_stat(task[1])
            elif task[0] == 'LS':
                self.do_ls(task[1])
            elif task[0] == 'LS-R':
                self.do_ls_r(task[1])
            elif task[0] == 'RENAME':
                self.do_rename(task[1], task[2])
            elif task[0] == 'REMOVE':
                self.do_delete(task[1])
            elif task[0] == 'EXIT':
                self.close()
                logging.debug("Exit.")
                self.task_q.task_done()
                return
            else:
                msg = "Invalid task: %s" % str(task)
                logging.error(msg)
                TestClient.ERRORS.append(msg)

            self.task_q.task_done()
            #time.sleep(1)

################################## MAIN ###################################
PROGRAM=os.path.basename(sys.argv[0])

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#parser.add_argument('-r', action='store_true')
parser.add_argument('OPERATOR', choices=['.upload', '.download', '.rm', '.stat', '.ls', '.lsr', '.rename'])
parser.add_argument('FILE', nargs='+')
parser.add_argument('-H', dest='HOST', required=True, help='remote host')
parser.add_argument('-v', action='count', default=0)
parser.add_argument('--threads', '-t', type=int, default=1, help='Number of worker threads')
ARGS = parser.parse_args()

threading.current_thread().name = "M"
if ARGS.v>0:
    lvl=logging.DEBUG
else:
    lvl=logging.INFO
logging.basicConfig(format=' [%(asctime)s.%(msecs)03d@%(threadName)s] %(message)s', datefmt='%H:%M:%S', level=lvl)
logging.info(ARGS)

q = Queue()
for i in range(ARGS.threads):
    t = TestClient(ARGS.HOST, '9091', q)
    #t.daemon = True
    t.start()
    #time.sleep(1)

if ARGS.OPERATOR == '.upload':
    if len(ARGS.FILE)==1:
        for f in ARGS.FILE:
            q.put(['UPLOAD', f, '/'])
    else:
        for f in ARGS.FILE[0:-1]:
            q.put(['UPLOAD', f, ARGS.FILE[-1]])
if ARGS.OPERATOR == '.download':
    if len(ARGS.FILE)==1:
        for f in ARGS.FILE:
            q.put(['DOWNLOAD', f, '.'])
    else:
        for f in ARGS.FILE[0:-1]:
            q.put(['DOWNLOAD', f, ARGS.FILE[-1]])
elif ARGS.OPERATOR == '.rm':
    q.put(['REMOVE', ARGS.FILE])
elif ARGS.OPERATOR == '.stat':
    for f in ARGS.FILE:
        q.put(['STAT', f])
elif ARGS.OPERATOR == '.ls':
    for f in ARGS.FILE:
        q.put(['LS', f])
elif ARGS.OPERATOR == '.lsr':
    for f in ARGS.FILE:
        q.put(['LS-R', f])
elif ARGS.OPERATOR == '.rename':
    if len(ARGS.FILE)!=2:
        print(".rename path newFileName")
        exit(1)
    q.put(['RENAME', ARGS.FILE[0], ARGS.FILE[1]])

q.join()

############################# RESULT ##########################
print("======================= ERRORS: %d ======================" % len(TestClient.ERRORS))
for msg in TestClient.ERRORS:
    print(msg)
############################# CLEAN UP ##########################
for i in range(ARGS.threads):
    q.put(['EXIT'])
logging.debug("Finished.")
