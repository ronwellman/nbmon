#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
    logger  -   generic module for writing log entries

        format: YYYY-mm-dd HH:MM:SS UTC - message
            Timezone is always in UTC
            Clock is always 24 hours

    Copyright 2017 Ron Wellman
'''
import datetime

def generate_log(msg, severity):
    '''
        creates or appends a log file entries
    '''
    with open('nbmon.log','a') as f:
        f.write('{:%Y-%m-%d %H:%M:%S} UTC - {} - {}\n'.format(datetime.datetime.utcnow(), severity.upper(), msg))