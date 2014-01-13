#!/usr/bin/env python2
#coding: utf-8

import os
import MySQLdb
from flask import Flask, request, redirect, render_template_string, \
    url_for, send_file
from proj.tasks import files_diff
from proj.fmtDiff import parse_diff_result
from proj import db, config


app = Flask(__name__)
app.debug = True

    
def get_template_string(key):
    filename_dict = {
        'template' : 'templates/template.html',
        'upload-form' : 'templates/upload-form.html'
    }
    template_file = open(filename_dict[key], 'r')
    HTML_TEMPLATE = template_file.read()
    template_file.close()
    return HTML_TEMPLATE


@app.route('/')
def index():
    rid = request.args.get('rid', '0')
    html_template_string = get_template_string('template')
    db_cli = db.MySqlClient(config.MYSQL_CONN)
    db_cli.connect()
    diff_record = db_cli.get_record(rid)
    db_cli.close()

    fn1, fn2, res1, res2, html_res1, html_res2, dt = diff_record[0] if len(diff_record) == 1 else (None, None, None, None, None, None, None)
    lines1, lines2 = parse_diff_result(res1), parse_diff_result(res2)
    return render_template_string(html_template_string,
                                  fn1=fn1, fn2=fn2, dt=dt,
                                  lines1=lines1, lines2=lines2,
                                  html_res1=html_res1, html_res2=html_res2)

    
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']
        fn1 = file1.filename.encode('utf-8')
        fn2 = file2.filename.encode('utf-8')
        filepath1 = os.path.join(config.UPLOAD_PATH, fn1)
        filepath2 = os.path.join(config.UPLOAD_PATH, fn2)
        file1.save(filepath1)
        file2.save(filepath2)
        
        res = files_diff.delay(filepath1, filepath2)
        rid = res.get()
        return redirect(url_for('.index', rid=rid))
    else:
        html_template_string = get_template_string('upload-form')
        return render_template_string(html_template_string)

    
    
@app.route('/Diff-Formatter.tar.gz')
def download_tar():
    tarcmd = 'cd %s && tar -zcf Diff-Formatter-dev.tar.gz Diff-Formatter-dev' % config.PROJECT_PATH
    os.system(tarcmd)
    return send_file('%s/Diff-Formatter-dev.tar.gz' % config.PROJECT_PATH)
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765)
