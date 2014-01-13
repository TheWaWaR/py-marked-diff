#!/usr/bin/env python2
#coding: utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import uuid
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
    uuid = request.args.get('uuid', None)
    record = MarkedDiff.query.filter_by(uuid=uuid).first()
    if record is None:
        return redirect(url_for('.upload'))
        
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
        prefix = uuid.uuid1().hex
        if fn1 == fn2:
            fn1 = '1.%s' % fn1
            fn2 = '2.%s' % fn2
        fn1 = '%s--%s' % (prefix, fn1)
        fn2 = '%s--%s' % (prefix, fn2)
        filepath1 = os.path.join(UPLOAD_PATH, fn1)
        filepath2 = os.path.join(UPLOAD_PATH, fn2)
        file1.save(filepath1)
        file2.save(filepath2)
        
        data = process_files_diff(filepath1, filepath2)
        data['uuid'] = prefix
        record = MarkedDiff()
        record.save(data)
        return redirect(url_for('.index', uuid=record.uuid))
    else:
        return render_template('upload-form.html')

        
if __name__ == '__main__':
    if len(sys.argv) == 2:
        db.create_all()
        print 'Table created'
        sys.exit(1)
    app.run(host='0.0.0.0', port=8765)
