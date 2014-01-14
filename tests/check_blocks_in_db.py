#!/usr/bin/env python
#coding: utf-8

import sys
import json
import sqlite3

db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
c = conn.cursor()
r = c.execute('select blocks1, blocks2 from marked_diffs where id=%s;' % sys.argv[2])

for record in [_t for _t in r]:
    data1, data2 = record
    blocks1 = json.loads(data1)
    blocks2 = json.loads(data2)
    for b in blocks1:
        for line in b:
            print line
        print '-'*10
    print '='*20
    
    for b in blocks2:
        for line in b:
            print line
        print '-'*10
    
r.close()    
c.close()

