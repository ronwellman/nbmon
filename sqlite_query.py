#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlite_gen import Base, Device, Config
'''
    sqlite_query.py -> retreaves data from the device and device type tables

    Copyright 2017 Ron Wellman
'''
engine = create_engine('sqlite:///nbmon.db')
Base.metadata.bind = engine

DBSession = sessionmaker()
DBSession.bind = engine
session = DBSession()

def next_active_device():
    '''
        generator that returns all the active devices in the database
    '''
    for device in session.query(Device).filter(Device.actively_poll == True):
        yield device

def next_config(device_id):
    '''
        generator that returns all the configs for a specific device
    '''
    for config in session.query(Config).filter(Config.device_id == device_id).order_by('time_stamp'):
        yield config
