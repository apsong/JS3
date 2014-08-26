#! /usr/bin/env python3.4

import http.client
import sys
import json

class TestClient:
    host = None
    port = None
    conn = None
    token = None

    def __init__(self, host, port=None):
        self.host = host
        self.port = port
        self.conn = http.client.HTTPSConnection(self.host, self.port)

    def close(self):
        self.conn.close()

    def user_authorize(self, userid, password):
        self.conn.request("POST", "/api?method=user.authorize", \
            '{"userid":"%s","password":"%s"}' % (userid, password),\
            {"Content-type":"application/json"})
        resp = self.conn.getresponse()
        if (resp.code != 200):
            print("Error: " + str(resp.code) + " " + resp.reason)
            return

        data = resp.read().decode()
        dict = json.loads(data)
        self.token = dict['response']['token']

    def doc_query(self, merchantid, is_print):
        self.conn.request("POST", "/api?method=doc.query&token="+self.token,\
            '{"query":{"metadata.parameter.merchantid":"%s"}}' % merchantid,\
            {"Content-type":"application/json"})
        resp = self.conn.getresponse()
        if (resp.code != 200):
            print("Error: " + str(resp.code) + " " + resp.reason)
            return

        if (is_print):
            data = resp.read().decode()
            dict = json.loads(data)
            #print(json.dumps(dict, indent=2))
            print(" ".join([e['filename'] for e in dict['response']]))

def get_merchantids():
    pass

tc = TestClient("192.168.99.241", 9091)
tc.user_authorize('test', 'test')
tc.doc_query('999290055110006', True)
tc.close()
