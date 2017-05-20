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

import sys
import datetime
import click
import db.sqlite_query as db
from db.sqlite_fill import load_database
from utils.util import *

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
            generate_log(logfile, 'NBMON started - DAEMON', 'INFO')
        for device in db.next_active_device():

                config = get_config(device, logfile)
                if config == None:
                    continue

                timestamp = datetime.datetime.utcnow()
                hconfig = generate_hash(config)

                #Compare newly hashed config to the last one entered into the db
                if not db.compare_config(device,hconfig):
                    print 'CHANGE TO "%s": Inserting new config into DB' % device.description
                    db.insert_config(device, hconfig, config, timestamp)
                    generate_log(logfile, '{} configuration change'.format(device.ip), 'WARNING')
                else:
                    db.update_timestamp(device, timestamp)
    #display status
    elif status:
        if verbose:
            generate_log(logfile, 'NBMON started - STATUS', 'INFO')
        display_status()

    #input devices using a json formated file
    elif inputfile:
        load_database(inputfile)
        display_status()

    #clear all the counters
    elif clear:
        if verbose:
            generate_log(logfile, 'NBMON started - CLEAR', 'INFO')
        clear_counters()

    #edit the database
    elif edit:
        if verbose:
            generate_log(logfile, 'NBMON started - EDIT', 'INFO')
        edit_device(logfile, verbose)

    #no arguements
    else:
        print 'At least one argument required: python nbmon.py --help'

    if verbose:
        generate_log(logfile, 'NBMON exited with code {}'.format(exit_code), 'INFO')

    return(exit_code)

if __name__ == '__main__':

    exit_code = cli()
    if exit_code:
        sys.exit(exit_code)
    else:
        sys.exit(1)
