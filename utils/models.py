#coding: utf-8

from datetime import datetime
from .gvars import db

class MarkedDiff(db.Model):
    __tablename__ = 'marked_diffs'
    
    id           = db.Column(db.Integer, primary_key=True)
    uuid         = db.Column(db.String(32))
    filename1    = db.Column(db.String(100))
    filename2    = db.Column(db.String(100))
    blocks1      = db.Column(db.Text)
    blocks2      = db.Column(db.Text)
    html_result1 = db.Column(db.Text)
    html_result2 = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.now)

    def save(self, data):
        for k, v in data.iteritems():
            setattr(self, k, v)
        db.session.add(self)
        db.session.commit()
