#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
    sqlite_query.py -> retreaves data from the device and device type tables

    Copyright 2017 Ron Wellman
'''

from sqlalchemy import create_engine, text, desc
from sqlalchemy.orm import sessionmaker
from sqlite_gen import Base, Device, Config

def get_session(database='sqlite:///nbmon.db'):
    '''
        returns a session object to the database (defaulted to sqlite:///nbmon.db)
    '''
    engine = create_engine(database)
    Base.metadata.bind = engine
    DBSession = sessionmaker()
    DBSession.bind = engine
    return DBSession()

def next_active_device():
    '''
        generator that returns all the active devices in the database
    '''
    for device in session.query(Device).filter(Device.actively_poll == True):
        yield device

def next_config(device):
    '''
        generator that returns all the configs for the device
    '''
    for config in device.configs:
        yield config

def next_missed_device():
    '''
        generator that returns devices with missed_polls
    '''
    for device in session.query(Device).filter(Device.actively_poll == True and \
        ((Device.missed_polls != 0) or (Device.config_changes != 0))):

        yield device

def insert_config(device, hconf, conf, ts):
    '''
        inserts a new config into the config table, update the config_changes counter,
        and update the last_seen timestamp
    '''
    #uses the relationship between devices and configs to insert a new config for that object
    device.configs.append(Config(hconfig=hconf, config=conf, timestamp=ts))
    device.last_seen = ts
    device.config_changes += 1
    session.commit()

def compare_config(device, hconfig):
    '''
        returns True or False if the hashed config matches the latest hashed config
        for the device
    '''
    #checks the first config (object is presorted to descending based on timestamp)
    if device.configs and device.configs[0].hconfig == hconfig:
            return True
    else:
        return False

def update_timestamp(device, ts):
    '''
        updates the last_seen timestamp of a device
    '''
    device.last_seen = ts
    session.commit()

def missed_poll(device):
    '''
        updates the missed_polls counter
    '''
    device.missed_polls += 1
    session.commit()

#connects to the database and renders a session object for manipulation
session = get_session()
