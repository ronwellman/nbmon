#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
    sqlite_query.py -> interacts with the database

    Copyright 2017 Ron Wellman
'''

from sqlalchemy import create_engine, text, desc, delete
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

def next_device():
    '''
        generator that returns all devices in the database
    '''
    for device in session.query(Device):
        yield device

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
    for device in session.query(Device).filter(Device.actively_poll == True).order_by(Device.missed_polls.desc(),Device.config_changes.desc()):
        yield device

def insert_config(device, hconf, conf, ts):
    '''
        inserts a new config into the config table, update the config_changes counter,
        and update the last_seen timestamp
    '''
    #uses the relationship between devices and configs to insert a new config for that object
    device.configs.append(Config(hconfig=hconf, config=conf, timestamp=ts))
    device.last_seen = ts
    if len(device.configs) > 1:
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

def delete_config(config):
    '''
        deletes a config from the database
    '''
    session.delete(config)
    session.commit()

def update_timestamp(device, ts):
    '''
        updates the last_seen timestamp of a device
    '''
    device.last_seen = ts
    session.commit()

def update_device(device, field, value):
    '''
        updates a specific field of a device
    '''

    if field == 'device_type':
        device.device_type = value
    elif field == 'ip':
        device.ip = value
    elif field == 'port':
        device.port = value
    elif field == 'description':
        device.description = value
    elif field == 'username':
        device.username = value
    elif field == 'password':
        device.password = value
    elif field == 'secret':
        device.secret = value
    elif field == 'actively_poll':
        device.actively_poll = value
    elif field == 'missed_polls':
        device.missed_polls = value
    elif field == 'config_changes':
        device.config_changes = value
    session.commit()

def missed_poll(device):
    '''
        updates the missed_polls counter
    '''
    device.missed_polls += 1
    session.commit()

def clear_counters(device):
    '''
        zeroes out the counters for the device
    '''
    device.missed_polls = 0
    device.config_changes = 0
    session.commit()

def delete_device(device):
    '''
        remove a device from the database
    '''
    session.delete(device)
    session.commit()

#connects to the database and renders a session object for manipulation
session = get_session()
