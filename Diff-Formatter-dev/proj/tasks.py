#!/usr/bin/env python2
#coding: utf-8

from __future__ import absolute_import

import sys
from proj.celery import celery
from proj.fmtDiff import process_files_diff


@celery.task()
def files_diff(filename1, filename2):
    return process_files_diff(filename1, filename2)
