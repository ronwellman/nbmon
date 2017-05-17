#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
    sqlite_gen.py -> Utilize sqlalchemy to build the sqlite db file

    Tables:
        device
            device_id   - Integer   - pk
            device_type - String
            ip          - String
            port        - Integer
            description - String
            username    - String
            password    - String
            secret      - String
            actively_poll   - Boolean
            last_seen   - DateTime
            missed_polls    - Integer
            config_changes  - Integer

        config
            config_id   - Integer   - pk
            device_id   - Integer   - fk
            timestamp   - DateTime
            hconfig     - String
            config_id   - Text

    Relationships:
        Device.configs  -> Config
        Config.device   -> Device

    Copyright 2017 Ron Wellman
'''

from sqlalchemy import Table, Column, ForeignKey, desc
from sqlalchemy import Text, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

class Device(Base):
    __tablename__ = 'device'
    device_id = Column(Integer, primary_key=True)
    device_type = Column(String(32), nullable=False)
    ip = Column(String(19), nullable=False)
    port = Column(Integer)
    description = Column(String(100))
    username = Column(String(50), nullable=False)
    password = Column(String(128), nullable=False)
    secret = Column(String(128))
    actively_poll = Column(Boolean)
    last_seen = Column(DateTime)
    missed_polls = Column(Integer)
    config_changes = Column(Integer)

class Config(Base):
    __tablename__ = 'config'
    config_id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('device.device_id'))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    hconfig = Column(String(128), nullable=False)
    config = Column(Text, nullable=False)
    device = relationship(Device, back_populates="configs")

Device.configs = relationship(Config, order_by=desc(Config.timestamp), back_populates="device")

engine = create_engine("sqlite:///nbmon.db")
Base.metadata.create_all(engine)
