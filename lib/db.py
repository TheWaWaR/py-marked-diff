#!/usr/bin/env python2
#coding: utf-8

from __future__ import absolute_import

import MySQLdb
# import sqlite3
from proj.config import DIFF_TABLE_NAME

class MySqlClient():
    def __init__(self, config = {}):
        self.host = config.get('host')
        self.user = config.get('user')
        self.passwd = config.get('passwd')
        self.db = config.get('db')
        self.charset = config.get('charset', 'utf-8')

    def connect(self):
        self.conn =  MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd,
                                     db=self.db, charset=self.charset)
    def close(self):
        self.conn.close()
        
    def create_table(self):
        cursor = self.conn.cursor()
        SQL = '''CREATE TABLE IF NOT EXISTS %s (
            id int AUTO_INCREMENT PRIMARY KEY,
            filename1 VARCHAR(100),
            filename2 VARCHAR(100),
            result1 TEXT,
            result2 TEXT,
            html_result1 TEXT,
            html_result2 TEXT,
            datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );''' % DIFF_TABLE_NAME
        cursor.execute(SQL)
        self.conn.commit()
        cursor.close()

    
    def save_record(self, record):
        cursor = self.conn.cursor()
            
        SQL = 'INSERT INTO '+ DIFF_TABLE_NAME + '''
            (filename1, filename2, result1, result2, html_result1, html_result2)
            VALUES (%s, %s, %s, %s, %s, %s);'''
        cursor.execute(SQL, record)
        rid = cursor.lastrowid
        self.conn.commit()
        cursor.close()
        return rid
    
        
    def get_record(self, rid):
        cursor = self.conn.cursor()
        SQL = 'select filename1, filename2, result1, result2, html_result1, html_result2, datetime from %s WHERE id=%s' % (DIFF_TABLE_NAME, rid)
        cursor.execute(SQL)
        record = cursor.fetchall()
        self.conn.commit()
        cursor.close()
        return record
    
    
# ==============================================================================
#  SQLite3
# ==============================================================================
class SQLite3Client():
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        # self.conn = sqlite3.connect(self.db_path)
        pass

    def close(self):
        self.conn.close()

    def create_table(self):
        pass
        
    def save_record(self, record):
        pass

    def get_record(self, record):
        pass
