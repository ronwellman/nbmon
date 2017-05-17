#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
    Network Baseline Monitor Utilities

    Copyright 2017 Ron Wellman
'''
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
from hashlib import sha512
import datetime
import db.sqlite_query as db

def get_config(device, logfile):
    '''
        Connects to a device and returns its config
    '''
    if device.device_type == 'cisco_ios':
        #device contains extra fields that cause issues with netmiko
        fields = ('device_type','ip','username', 'password','port','secret')

    new_device = {}
    old_device = device.__dict__

    #pulling required fields out and placing in a new dictionary
    for f in fields:
        new_device[f] = old_device.pop(f)

    try:
        net_connect = ConnectHandler(**new_device)
        return net_connect.send_command('show running-config')
    except NetMikoTimeoutException as e:
        generate_log(logfile, e, 'WARNING')
        db.missed_poll(device)
        return None

def get_hash(config):
    '''
        return the sha512 hexdigest of the input text
    '''
    return sha512(config).hexdigest()

def display_status():
    '''
        build a display showing devices that are active and have either missed a poll or had a configuration change
    '''
    print ('{:^6}  {:^15}  {:^25}  {:^23}  {:^6}  {:^7}'.format('DEVICE','IP','DESCRIPTION','LAST_SEEN','MISSED', 'CHANGES'))
    for device in db.next_missed_device():

        if len(device.description) > 25:
            description = device.description[:26]
        else:
            description = device.description
        if device.last_seen:
            print('{:>6}  {:<15}  {:<25}  {:%Y-%m-%d %H:%M:%S} UTC  {:>6}  {:>7}'.format(\
                device.device_id, device.ip, description, device.last_seen,
                device.missed_polls, device.config_changes))
        else:
            print('{:>6}  {:<15}  {:<25}  {:^23}  {:>6}  {:>7}'.format(\
                device.device_id, device.ip, description, 'NEVER',
                device.missed_polls, device.config_changes))


def generate_log(logfile, msg, severity):
    '''
        writes an entry to the log
    '''

    logfile.write('{:%Y-%m-%d %H:%M:%S} UTC - {} - {}\n'.format(datetime.datetime.utcnow(), severity.upper(), msg))
