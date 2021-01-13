#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manage the DT78 from the command line
Alarm spec: set|reset timespec [days]
  Omitting days will program a single alarm
  days: day1-day2 makes a range of days
        day1,day2,... selects specific days
"""
import pygatt
import time
import sys
import argparse
import re

tspecRe    = re.compile(r'^((0?[0-9]|1[0-9]|2[0-3])):([0-5][0-9])$')
tparse_re  = re.compile(r'([0-9]+):([0-9]+)')

tsingle_re = re.compile(r'^(Mo|Tu|We|Th|Fr|Sa|Su)((,(Mo|Tu|We|Th|Fr|Sa|Su))*)$')
tspan_re   = re.compile(r'(Mo|Tu|We|Th|Fr|Sa|Su)-(Mo|Tu|We|Th|Fr|Sa|Su)')
dspecRe    = re.compile(r'^(Mo|Tu|We|Th|Fr|Sa|Su)([-](Mo|Tu|We|Th|Fr|Sa|Su)|(,(Mo|Tu|We|Th|Fr|Sa|Su))+)?$')

weekdays = ['Mo','Tu','We','Th','Fr','Sa','Su']

def bool_flag(val):
    return f'{1 if val else 0:02x}'

def send_cmd(cmd,args,adapter=None):
    if args.verbose: print(f'char-write-req 0x{args.tx_channel:04x} {cmd}')
    adapter.sendline(f'char-write-req 0x{args.tx_channel:04x} {cmd}')

def set_time(args,adapter=None):
    assert adapter is not None, "Invalid adapter"
    #
    #
    # Get the time from the system now and refresh the device
    #
    now = time.localtime()
    cmd1  = f'AB000BFF938000{now.tm_year:04X}{now.tm_mon:02X}{now.tm_mday:02X}'
    cmd1 += f'{now.tm_hour:02X}{now.tm_min:02X}{now.tm_sec:02X}'

    print('Setting time')
    send_cmd(cmd1, args, adapter=adapter)

    cmd2 = f'AB0004FF7C80'+bool_flag(args.set12)
    print(f'Setting {12 if args.set12 else 24}h mode')
    send_cmd(cmd2, args, adapter=adapter)

    if args.find:
        print('And now.. try to find the watch...')
        send_cmd('AA0003FF7180', args, adapter=adapter)


def set_alarm(args,adapter=None):
    # assert adapter is not None, 'Invalid adapter'
    action_hour, action_min = 0, 0
    action_days = 0
    day_bits = 0
    action_set = args.alarm[0] == 'set'
    match_tparse = tparse_re.match(args.alarm[1])
    # print(match_tparse)
    action_hour = int(match_tparse.group(1))
    action_min = int(match_tparse.group(2))
    # print (f'{action_hour}:{action_min:02d}', file=sys.stdout)
    try:
        #
        # Try repeating alarm
        #
        match_span   = tspan_re.match(args.alarm[2])
        day_bits = 0
        if match_span is not None:
            day1,day2 = weekdays.index(match_span.group(1)),weekdays.index(match_span.group(2))
            if day2 < day1:
                tmp = day2
                day2 = day1
                day1 = tmp
            for i in range(day1, day2+1):
                day_bits |= 1 << i
        else:
            day_spec = args.alarm[2]
            while True:
                match_days = tsingle_re.match(day_spec)
                this_day = weekdays.index(match_days.group(1))
                day_bits |= 1 << this_day
                # print(f'{match_days.groups()} {this_day} {day_bits:02x}')
                day_spec = match_days.group(2)[1:]
                if match_days.group(3) == None: break
    except:
        #
        # Set single alarm
        #
        day_bits = 0x80
    cmd = 'AB0008FF738000{bool_flag(action_set)}{action_hour:02x}{action_min:02x}{day_bits:02x}'
    send_cmd (cmd, args, adapter=adapter)

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-1', '--12',  dest='set12',
                        action='store_true',
                        help='Set 12h mode')
    parser.add_argument('-f', '--find',  dest='find',
                        action='store_true', help='Find the watch before quiting')
    parser.add_argument('-V', '--verbose',  dest='verbose',
                        action='store_true', help='Print all info')
    parser.add_argument('-m', '--mac', dest='mac',
                        type=str, default='E8:83:55:62:68:98',
                        help='The MAC address')
    parser.add_argument('-t', '--tx',  dest='tx_channel',
                        type=int, default=0x15,
                        help='The TX channel')
    parser.add_argument("action", metavar="ACTION",
                        type=str, help="'set' to set the time 'alarm' to manage alarms")

    parser.add_argument("alarm", metavar="ALARM",
                        type=str, nargs="*", help="The alarm spec")

    args = parser.parse_args()

    assert args.action in ['set','alarm'],f'Unknown action {args.action}'
    if args.action == 'set':
        assert len(args.alarm) == 0, 'Set action is for time. Use alarm set for alarms'
    else:
        #
        # Alarm handling
        #
        assert args.alarm[0] in ['set','reset'], 'Alarms can only be set or reset'
        assert len(args.alarm) in range(2,4), 'alarm [re]set <tspec> [<days>]'
        assert tspecRe.match(args.alarm[1]), f'wrong tspec {args.alarm[1]}'
        if len(args.alarm) == 3:
            assert dspecRe.match(args.alarm[2]), f'wrond day spec {args.alarm[2]}'

    adapter = pygatt.GATTToolBackend()
    adapter.start()
    while True:
        try:
            device = adapter.connect(args.mac, timeout=10,  address_type=pygatt.BLEAddressType.random)
            break
        except pygatt.exceptions.NotConnectedError:
            print('Waiting...')
        except IndexError:
            print ('MAC missing...')
            raise SystemExit
        except KeyboardInterrupt:
            adapter.stop()
            raise SystemExit

    print(f'Connected to {args.mac}...')
    if args.action == 'set':
        set_time(args,adapter=adapter)
    else:
        set_alarm(args,adapter=adapter)
    adapter.stop()

if __name__ == "__main__":
    try:
        main()
    except AssertionError as aerr:
        print(aerr)
