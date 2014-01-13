#coding: utf-8


# ==============================================================================
#  Database 
# ==============================================================================
DIFF_TABLE_NAME = 'files_diff_output'

MYSQL_CONN = {
    'host'    : "192.168.100.71",
    'user'    : "root",
    'passwd'  : "public",
    'db'      : "ipon",
    'charset' : "utf8"
}

SQLITE_FILE = 'diffOutput.db'


# ==============================================================================
#  Paths
# ==============================================================================
PROJECT_PATH = '/root/Downloads'
UPLOAD_PATH = '/root/Downloads/Diff-Formatter-dev/upload'
