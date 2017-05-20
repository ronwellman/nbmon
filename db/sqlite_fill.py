#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
    sqlite_fill.py -> inserts devices into the database

    Copyright 2017 Ron Wellman
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.sqlite_gen import Base, Device, Config
import json

def load_database(inputfile):
    '''
        reads in a json formatted file, creates a new device object, and inserts it into the database
    '''

    engine = create_engine('sqlite:///nbmon.db')

    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)

    session = DBSession()

    load = json.load(inputfile)

    for device in load['devices']:
        new_device = Device(ip=device['ip'],port=device['port'],description=device['description'],
            username=device['username'],password=device['password'],
            actively_poll=device['actively_poll'],device_type=device['device_type'],
            secret=device['secret'],missed_polls=device['missed_polls'],
            config_changes=device['config_changes'])
        session.add(new_device)
        session.commit()
