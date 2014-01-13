#!/usr/bin/env python2
#coding: utf-8

from __future__ import absolute_import

from celery import Celery

celery = Celery('proj.celery',
                borker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0',
                include=['proj.tasks'])

if __name__ == '__main__':
    celery.start()
