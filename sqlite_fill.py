#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlite_gen import Base, Device, Config
'''
    sqlite_fill.py -> inserts data into the device_type and device tables

    Copyright 2017 Ron Wellman
'''

engine = create_engine('sqlite:///nbmon.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

#device table
new_device = Device(ip='192.168.100.11',description='Cisco 2600 in Rack 1',
    username='cisco',password='cisco',actively_poll=True,device_type='cisco_ios',
    secret='cisco',missed_polls=0,config_changes=0)
session.add(new_device)
session.commit()
new_device = Device(ip='192.168.100.12',description='Cisco 2600 in Rack 2',
    username='cisco',password='cisco',actively_poll=False,device_type='cisco_ios',
    secret='cisco',missed_polls=0,config_changes=0)
session.add(new_device)
session.commit()
new_device = Device(ip='192.168.100.13',description='Cisco 2600 in Rack 3',
    username='cisco',password='cisco',actively_poll=False,device_type='cisco_ios',
    secret='cisco',missed_polls=0,config_changes=0)
session.add(new_device)
session.commit()
new_device = Device(ip='192.168.100.14',description='Cisco 2600 in Rack 4',
    username='cisco',password='cisco',actively_poll=False,device_type='cisco_ios',
    secret='cisco',missed_polls=0,config_changes=0)
session.add(new_device)
session.commit()
