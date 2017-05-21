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
import click
import ipaddress
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

def generate_hash(config):
    '''
        return the sha512 hexdigest of the input text
    '''
    return sha512(config).hexdigest()

def display_status():
    '''
        build a display showing devices that are active and have either missed a poll or had a configuration change
    '''
    #header
    output = '{:^6}  {:^15}  {:^25}  {:^23}  {:^6}  {:^7}'.format('DEVICE','IP','DESCRIPTION','LAST_SEEN','MISSED', 'CHANGES')

    for device in db.next_missed_device():

        if len(device.description) > 25:
            description = device.description[:26]
        else:
            description = device.description

        if device.last_seen:
            #accumulate output
            output = '\n'.join([output,'{:>6}  {:<15}  {:<25}  {:%Y-%m-%d %H:%M:%S} UTC  {:>6}  {:>7}'.format(\
                device.device_id, device.ip, description, device.last_seen,
                device.missed_polls, device.config_changes)])
        else:
            #accumulate output
            output = '\n'.join([output,'{:>6}  {:<15}  {:<25}  {:^23}  {:>6}  {:>7}'.format(\
                device.device_id, device.ip, description, 'NEVER',
                device.missed_polls, device.config_changes)])

    #generates pages of output rather than overwhelming the screen
    click.echo_via_pager(output)

def clear_counters():
    '''
        clear the counters of all devices
    '''
    for device in db.next_device():
        db.clear_counters(device)

def edit_device(logfile, verbose):
    '''
        iterates through the devices and allows for changes to be made
    '''
    edit = {'2':'device_type','3':'ip','4':'port','5':'description',\
            '6':'username','7':'password','8':'secret','9':'actively_poll',\
            '10':'last_seen','11':'missed_polls','12':'config_changes'}
    for device in db.next_device():
        #outer loop to keep same device loaded in the menu
        while True:
            print_edit_menu(device)

            choice = click.prompt('What would you like to do').upper()

            if choice == 'N':
                #outer break
                break
            elif choice == 'Q':
                return None
            elif choice == 'V' or choice == '13':
                print_config_menu(device)
            elif choice == 'D':
                if verbose:
                    msg = 'Device {} deleted.'.format(device.device_id)
                    generate_log(logfile, msg, 'INFO')
                db.delete_device(device)
                break
            elif choice =='2':
                value = validate_device_type(device)
                if value:
                    if verbose:
                        msg = 'Device {} type modified from "{}" to "{}".'.format(device.device_id, device.device_type, value)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], value)
            elif choice =='3':
                value = validate_ip_address(device)
                if value:
                    if verbose:
                        msg = 'Device {} IP modified from "{}" to "{}".'.format(device.device_id, device.ip, value)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], value)
            elif choice =='4':
                value = validate_port(device)
                if value:
                    if verbose:
                        msg = 'Device {} Port modified from "{}" to "{}".'.format(device.device_id, device.port, value)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], value)
            elif choice =='5':
                value = validate_description(device)
                if value:
                    if verbose:
                        msg = 'Device {} description modified from "{}" to "{}".'.format(device.device_id, device.description, value)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], value)
            elif choice =='6':
                value = validate_username(device)
                if value:
                    if verbose:
                        msg = 'Device {} username modified from "{}" to "{}".'.format(device.device_id, device.username, value)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], value)
            elif choice =='7':
                value = validate_password(device)
                if value:
                    if verbose:
                        msg = 'Device {} password changed.'.format(device.device_id)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], value)
            elif choice =='8':
                value = validate_secret(device)
                if value:
                    if verbose:
                        msg = 'Device {} secret changed.'.format(device.device_id)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], value)
            elif choice =='9':
                value = validate_actively_poll(device)
                if value != None:
                    if verbose:
                        msg = 'Device {} actively_poll modified from "{}" to "{}".'.format(device.device_id, device.actively_poll, value)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], value)
            elif choice =='10':
                value = validate_last_seen(device)
                if value != None:
                    if verbose:
                        msg = 'Device {} last_seen cleared.'.format(device.device_id)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], None)
            elif choice =='11':
                value = validate_missed_polls(device)
                if value != None:
                    if verbose:
                        msg = 'Device {} missed_polls cleared.'.format(device.device_id)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], 0)
            elif choice =='12':
                value = validate_config_changes(device)
                if value != None:
                    if verbose:
                        msg = 'Device {} config_changes cleared.'.format(device.device_id)
                        generate_log(logfile, msg, 'INFO')
                    db.update_device(device, edit[choice], 0)
            else:
                print('\nInvalid Entry\n')
                click.pause()


def print_edit_menu(device):
    '''
        builds a menu for editing a device
    '''
    total = len(device.configs)

    click.clear()
    print('[DEVICE]')
    print('==============================================')
    click.echo(click.style(' 1 - Device ID      : {}'.format(device.device_id), fg='red'))
    click.echo(click.style(' 2 - Device Type    : {}'.format(device.device_type), fg='green'))
    click.echo(click.style(' 3 - IP             : {}'.format(device.ip), fg='green'))
    click.echo(click.style(' 4 - Port           : {}'.format(device.port), fg='green'))
    click.echo(click.style(' 5 - Description    : {}'.format(device.description), fg='green'))
    click.echo(click.style(' 6 - Username       : {}'.format(device.username), fg='green'))
    click.echo(click.style(' 7 - Password       : {}'.format('**********'), fg='green'))
    click.echo(click.style(' 8 - Secret         : {}'.format('**********'), fg='green'))
    click.echo(click.style(' 9 - Actively Poll  : {}'.format(device.actively_poll), fg='green'))
    click.echo(click.style('10 - Last Seen      : {:%Y-%m-%d %H:%M:%S} UTC'.format(device.last_seen), fg='green'))
    click.echo(click.style('11 - Missed Polls   : {}'.format(device.missed_polls), fg='green'))
    click.echo(click.style('12 - Config Changes : {}'.format(device.config_changes), fg='green'))
    click.echo(click.style('13 - Num of Configs : {}'.format(total), fg='green'))
    print('==============================================')
    click.echo('Entries in ' + click.style('Red',fg='red') + ' cannot be changed')
    print('')
    print('<#> - Edit Value, <N> - Next, <V> - View Configs, <D> - Delete, <Q> - Quit')
    print('')

def validate_device_type(device):
    '''
        validates changes to the device type
    '''
    device_type = [[u'a10', u'alcatel_sros', u'arista_eos', u'aruba_os', u'avaya_ers'],\
        [u'avaya_vsp', u'brocade_fastiron', u'brocade_netiron', u'brocade_nos', u'brocade_vdx'],\
        [u'brocade_vyos', u'checkpoint_gaia', u'ciena_saos', u'cisco_asa', u'cisco_ios'],\
        [u'cisco_nxos', u'cisco_s300', u'cisco_tp', u'cisco_wlc', u'cisco_xe'],\
        [u'cisco_xr', u'dell_force10', u'dell_powerconnect', u'eltex', u'enterasys'],\
        [u'extreme', u'f5_ltm', u'fortinet', u'generic_termserver', u'hp_comware'],\
        [u'hp_procurve', u'huawei', u'juniper', u'juniper_junos', u'linux'],\
        [u'mellanox_ssh', u'ovs_linux', u'paloalto_panos', u'pluribus', u'quanta_mesh'],\
        [u'ubiquiti_edge', u'vyatta_vyos', u'vyos']]

    width = max(len(word) for row in device_type for word in row) + 2

    #continue to display valid device types until user aborts or chooses a valid type
    while True:
        click.clear()

        print('[DEVICE > DEVICE TYPE]')
        print('==============================================')
        click.echo(click.style(' 2 - Device Type    : {}'.format(device.device_type), fg='green'))
        print('==============================================')
        for row in device_type:
            click.echo(click.style(" ".join(word.ljust(width) for word in row), fg='green'))
        print('==============================================')
        print('<A> - Abort')
        print('')

        value = click.prompt('New value')

        if value.upper() == 'A':
            return None
        elif any(value in row for row in device_type):
            return value
        else:
            print('\nInvalid Entry\n')
            click.pause()

def validate_ip_address(device):
    '''
        validates changes to the ip address
    '''
    while True:
        click.clear()

        print('[DEVICE > IP ADDRESS]')
        print('==============================================')
        click.echo(click.style(' 3 - IP Address    : {}'.format(device.ip), fg='green'))
        print('==============================================')
        print('<A> - Abort')
        print('')

        value = click.prompt('New value')

        if value.upper() == 'A':
            return None
        else:
            #test for a valid ipv4 or ipv6 address
            try:
                ipaddress.ip_address(value)
                return value
            except Exception as e:
                print('\nInvalid Entry\n')
                click.pause()

def validate_port(device):
    '''
        validates changes to the port number
    '''
    while True:
        click.clear()

        print('[DEVICE > PORT]')
        print('==============================================')
        click.echo(click.style(' 4 - Port    : {}'.format(device.port), fg='green'))
        print('==============================================')
        print('<A> - Abort')
        print('')

        value = click.prompt('New value (1 - 49151)')

        if value.upper() == 'A':
            return None
        else:
            try:
                value = int(value)
                if value >= 1 and value <= 49151:
                    return value
                else:
                    print('\nInvalid Port Range\n')
                    click.pause()
            except:
                print('\nInvalid Entry\n')
                click.pause()

def validate_description(device):
    '''
        validates changes to description
    '''
    while True:
        click.clear()
        print('[DEVICE > DESCRIPTION]')
        print('==============================================')
        click.echo(click.style(' 5 - Description    : {}'.format(device.description), fg='green'))
        print('==============================================')
        print('<A> - Abort')
        print('')

        value = click.prompt('New value')

        if value.upper() == 'A':
            return None
        else:
            return value[:100]

def validate_username(device):
    '''
        validates changes to username
    '''
    while True:
        click.clear()
        print('[DEVICE > USERNAME]')
        print('==============================================')
        click.echo(click.style(' 6 - Username       : {}'.format(device.username), fg='green'))
        print('==============================================')
        print('<A> - Abort')
        print('')

        value = click.prompt('New value')

        if value.upper() == 'A':
            return None
        else:
            return value[:50]

def validate_password(device):
    '''
        validates changes to password
    '''
    while True:
        click.clear()
        print('[DEVICE > PASSWORD]')
        print('==============================================')
        click.echo(click.style(' 7 - Password       : {}'.format('**********'), fg='green'))
        print('==============================================')
        print('<A> - Abort')
        print('')

        value = click.prompt('New value')

        if value.upper() == 'A':
            return None
        else:
            return value[:128]

def validate_secret(device):
    '''
        validates changes to password
    '''
    while True:
        click.clear()
        print('[DEVICE > SECRET]')
        print('==============================================')
        click.echo(click.style(' 8 - Secret         : {}'.format('**********'), fg='green'))
        print('==============================================')
        print('<A> - Abort')
        print('')

        value = click.prompt('New value')

        if value.upper() == 'A':
            return None
        else:
            return value[:128]

def validate_actively_poll(device):
    '''
        validates changes to actively_poll
    '''
    while True:
        click.clear()

        print('[ACTIVELY POLL]')
        print('==============================================')
        click.echo(click.style(' 9 - Actively Poll  : {}'.format(device.actively_poll), fg='green'))
        print('==============================================')
        print('<A> - Abort, <T> - True, <F> - False')
        print('')

        choice = click.prompt('What would you like to do').upper()

        if choice == 'A':
            return None
        elif choice == 'T' or choice == 'TRUE':
            return True
        elif choice == 'F' or choice == 'FALSE':
            return False
        else:
            print('\nInvalid Entry\n')
            click.pause()

def validate_last_seen(device):
    '''
        validates changes to last_seen
    '''
    while True:
        click.clear()
        print('[DEVICE > LAST SEEN]')
        print('==============================================')
        click.echo(click.style('10 - Last Seen      : {}'.format(device.last_seen), fg='green'))
        print('==============================================')
        print('<A> - Abort, <C> - Clear')
        print('')

        choice = click.prompt('What would you like to do').upper()

        if choice == 'A':
            return None
        elif choice == 'C':
            return choice
        else:
            print('\nInvalid Entry\n')
            click.pause()

def validate_missed_polls(device):
    '''
        validates changes to missed_polls
    '''
    while True:
        click.clear()
        print('[DEVICE > MISSED POLLS]')
        print('==============================================')
        click.echo(click.style('11 - Missed Polls   : {}'.format(device.missed_polls), fg='green'))
        print('==============================================')
        print('<A> - Abort, <C> - Clear')
        print('')

        choice = click.prompt('What would you like to do').upper()

        if choice == 'A':
            return None
        elif choice == 'C':
            return choice
        else:
            print('\nInvalid Entry\n')
            click.pause()

def validate_config_changes(device):
    '''
        validates changes to config_changes
    '''
    while True:
        click.clear()
        print('[DEVICE > CONFIG CHANGES]')
        print('==============================================')
        click.echo(click.style('12 - Config Changes : {}'.format(device.config_changes), fg='green'))
        print('==============================================')
        print('<A> - Abort, <C> - Clear')
        print('')

        choice = click.prompt('What would you like to do').upper()

        if choice == 'A':
            return None
        elif choice == 'C':
            return choice
        else:
            print('\nInvalid Entry\n')
            click.pause()

def print_config_menu(device):
    '''
        builds a menu for showing the number of configs a device has
    '''
    counter = 0

    while True:
        total = (len(device.configs))
        click.clear()
        print('[DEVICE > CONFIGS]')
        print('==============================================')
        click.echo(click.style(' 1 - Device ID       : {}'.format(device.device_id), fg='red'))
        if total > 0:
            click.echo(click.style(' 2 - Config          : {} of {}'.format(counter + 1, total), fg='green'))
            click.echo(click.style(' 3 - Timestamp       : {:%Y-%m-%d %H:%M:%S} UTC'.format(device.configs[counter].timestamp), fg='red'))
        else:
            click.echo(click.style(' 2 - Config          : {} of {}'.format(counter, total), fg='red'))
            click.echo(click.style(' 3 - Timestamp       :', fg='red'))
        print('==============================================')
        if total > 0:
            print('<V> - View Config, <N> - Next, <P> - Previous, <D> - Delete Config, <Q> - Quit')
            print('')
        else:
            print('\nThere are no remaining configs.\n')
            click.pause()
            return None

        choice = click.prompt('What would you like to do').upper()

        if choice == 'Q':
            return None
        elif choice == 'N':
            counter += 1
            counter %= total
        elif choice == 'P':
            if counter > 0:
                counter -= 1
            else:
                counter = total - 1
        elif choice == 'D':
            db.delete_config(device.configs[counter])
            if counter > 0:
                counter -= 1

        elif choice == 'V' or choice == '2':
            click.echo_via_pager(device.configs[counter].config)
        else:
            print('\nInvalid Entry\n')
            click.pause()

def generate_log(logfile, msg, severity):
    '''
        writes an entry to the log
    '''
    logfile.write('{:%Y-%m-%d %H:%M:%S} UTC - {} - {}\n'.format(datetime.datetime.utcnow(), severity.upper(), msg))
