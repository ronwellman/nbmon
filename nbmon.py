#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
    nbmon   - Network Baseline Monitor
            - Can be used to monitor your network devices to periodically look for config_changes
            - Utilizes netmiko module to ssh into devices
            - Utilizes sqlite database for tracking of devices and config_changes
            - Utilizes sqlalchemy to interact with the database

            Parameters
                -d  - launch nbmon as a daemon
                -s  - display status (active and have either missed a poll or had a configuration change)
                -f  - load database via json formatted file
                -c  - clear all counters
                -e  - edit database

    Copyright 2017 Ron Wellman
'''
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
import sys
import argparse
import sqlite_query as db
from hashlib import sha512
import datetime
import logger

def get_config(device):
    '''
        Connects to a device and returns its config
    '''
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
        logger.generate_log(e, 'WARNING')
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

        print('{:>6}  {:<15}  {:<25}  {:%Y-%m-%d %H:%M:%S} UTC  {:>6}  {:>7}'.format(\
        device.device_id, device.ip, description, device.last_seen, device.missed_polls, device.config_changes))

def main(args):
    '''
        nbmon perations:

        check args
            -d
                loop through devices
                    get config
                    hash config
                    compare hash
                    record new config if hashes do not match
                    display status
    '''
    #daemonize
    if args.daemon:
        logger.generate_log('NBMON started - DAEMON', 'INFO')
        for device in db.next_active_device():

                config = get_config(device)
                if config == None:
                    continue

                timestamp = datetime.datetime.utcnow()
                hconfig = get_hash(config)

                #Compare newly hashed config to the last one entered into the db
                if not db.compare_config(device,hconfig):
                    print 'CHANGE TO "%s": Inserting new config into DB' % device.description
                    db.insert_config(device, hconfig, config, timestamp)
                    logger.generate_log('{} configuration change'.format(device.ip), 'WARNING')
                else:
                    db.update_timestamp(device, timestamp)

    elif args.status:
        logger.generate_log('NBMON started - STATUS', 'INFO')
        display_status()
    elif args.file:
        print args.file

    elif args.clear:
        logger.generate_log('NBMON started - CLEAR', 'INFO')
        for device in db.next_missed_device():
            db.clear_counters(device)

    elif args.edit:
        print args.edit
    else:
        print 'At least one argument required: python nbmon.py --help'

    return(None)

if __name__ == '__main__':
    #help menu and parameters
    parser = argparse.ArgumentParser(description='''nbmon - Network Baseline Monitor -
    Periodically monitor your network devices looking for changes in your network devices.''')
    parser.add_argument('-d','--daemon',help='launch nbmon as a daemon', action='store_true')
    parser.add_argument('-s','--status',help='display status of active devices', action='store_true')
    parser.add_argument('-f','--file', help='load database via json formatted file')
    parser.add_argument('-c','--clear', help='clear counters', action='store_true')
    parser.add_argument('-e','--edit', help='edit the database', action='store_true')
    args = parser.parse_args()

    exit_code = main(args)
    logger.generate_log('NBMON exited with code {}'.format(exit_code), 'INFO')
    sys.exit(exit_code)
