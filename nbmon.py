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
import sqlite_query as db
from hashlib import sha512
import datetime
import logger
import click
from sqlite_fill import load_database

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
        logger.generate_log(logfile, e, 'WARNING')
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

@click.command()
@click.option('--daemon', '-d', help='launch nbmon as a daemon', is_flag=True)
@click.option('--status', '-s', help='display status of active devices', is_flag=True)
@click.option('--inputfile', '-f', help='load database via json formatted file',type=click.File('r'))
@click.option('--clear', '-c', help='clear counters', is_flag=True)
@click.option('--edit', '-e', help='edit the database', is_flag=True)
@click.option('--logfile', '-l', help='use a custom log file',type=click.File('w'), default=sys.stdout)
@click.option('--verbose', '-v', help='enable verbose logging', is_flag=True)
def cli(daemon, status, inputfile, clear, edit, logfile, verbose):
    '''
        nbmon - Network Baseline Monitor

            Monitor your network devices looking for changes in your configurations
    '''
    exit_code = 0

    #daemonize
    if daemon:
        if verbose:
            logger.generate_log(logfile, 'NBMON started - DAEMON', 'INFO')
        for device in db.next_active_device():

                config = get_config(device, logfile)
                if config == None:
                    continue

                timestamp = datetime.datetime.utcnow()
                hconfig = get_hash(config)

                #Compare newly hashed config to the last one entered into the db
                if not db.compare_config(device,hconfig):
                    print 'CHANGE TO "%s": Inserting new config into DB' % device.description
                    db.insert_config(device, hconfig, config, timestamp)
                    logger.generate_log(logfile, '{} configuration change'.format(device.ip), 'WARNING')
                else:
                    db.update_timestamp(device, timestamp)

    elif status:
        if verbose:
            logger.generate_log(logfile, 'NBMON started - STATUS', 'INFO')
        display_status()

    elif inputfile:
        load_database(inputfile)
        display_status()
    elif clear:
        if verbose:
            logger.generate_log(logfile, 'NBMON started - CLEAR', 'INFO')
        for device in db.next_missed_device():
            db.clear_counters(device)

    elif edit:
        print args.edit
    else:
        print 'At least one argument required: python nbmon.py --help'

    if verbose:
        logger.generate_log(logfile, 'NBMON exited with code {}'.format(exit_code), 'INFO')

    return(exit_code)

if __name__ == '__main__':

    exit_code = cli()
    if exit_code:
        sys.exit(exit_code)
    else:
        sys.exit(1)
