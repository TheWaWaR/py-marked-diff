#!/usr/bin/env python2
#coding: utf-8

import sys
from proj.tasks import files_diff

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Arguments Error'
        sys.exit()
        
    filename1 = sys.argv[1]
    filename2= sys.argv[2]
    task_ret = files_diff.delay(filename1, filename2)
    print task_ret.get()
