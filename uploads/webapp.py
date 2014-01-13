#!/usr/bin/env python2
#coding: utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
from flask import (Flask, request, redirect, render_template,
                   url_for, send_file, abort)
from utils.fmtDiff import parse_diff_result, process_files_diff
from utils.gvars import db
from utils.models import MarkedDiff


app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
UPLOAD_PATH = os.path.join(app.root_path, 'uploads')

db.init_app(app)
db.app = app


@app.route('/')
def index():
    rid = request.args.get('rid', None)
    if rid is None:
        return redirect(url_for('.upload'))
        
    record = MarkedDiff.query.get_or_404(rid)
    lines1, lines2 = parse_diff_result(record.result1), parse_diff_result(record.result2)
    return render_template('main.html',
                           fn1=record.filename1,
                           fn2=record.filename2,
                           html_res1=record.html_result1,
                           html_res2=record.html_result2,
                           lines1=lines1, lines2=lines2,
                           dt=record.created_at)

    
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']
        fn1 = file1.filename.encode('utf-8')
        fn2 = file2.filename.encode('utf-8')
        filepath1 = os.path.join(UPLOAD_PATH, fn1)
        filepath2 = os.path.join(UPLOAD_PATH, fn2)
        file1.save(filepath1)
        file2.save(filepath2)
        
        record = process_files_diff(filepath1, filepath2)
        return redirect(url_for('.index', rid=record.id))
    else:
        return render_template('upload-form.html')

        
if __name__ == '__main__':
    if len(sys.argv) == 2:
        db.create_all()
        print 'Table created'
    app.run(host='0.0.0.0', port=8765)
