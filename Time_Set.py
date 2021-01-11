#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pygatt
import time
import sys
import argparse
from random import *
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
parser.add_argument("alarm", metavar="ALARM",
                    type=str, nargs="*", help="Set an alarm")

args = parser.parse_args()

# alarm_id = 1
# alarm_state = False
# alarm_hr = 0
# alarm_min = 0
# repeat = 0x02
# cmd3 = f'AB0008FF7380{alarm_id:02x}{1 if alarm_state else 0:02x}{alarm_hr:02x}{alarm_min:02x}{repeat:02x}'

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
#
#
# Get the time from the system now and refresh the device
#
now = time.localtime()
cmd1  = f'AB000BFF938000{now.tm_year:04X}{now.tm_mon:02X}{now.tm_mday:02X}'
cmd1 += f'{now.tm_hour:02X}{now.tm_min:02X}{now.tm_sec:02X}'
# print(cmd1)

print('Setting time')
if args.verbose: print(f'char-write-req 0x{args.tx_channel:04x} {cmd1}')
adapter.sendline(f'char-write-req 0x{args.tx_channel:04x} {cmd1}')

cmd2 = f'AB0004FF7C80{1 if args.set12 else 0:02x}'
# print(cmd2)
print(f'Setting {12 if args.set12 else 24}h mode')
if args.verbose: print(f'char-write-req 0x{args.tx_channel:04x} {cmd2}')
adapter.sendline(f'char-write-req 0x{args.tx_channel:04x} {cmd2}')

if args.find:
    cmd3 = f'AA0003FF7180'
    print('And now.. try to find the watch...')
    if args.verbose: print(f'char-write-req 0x{args.tx_channel:04x} {cmd3}')
    adapter.sendline(f'char-write-req 0x{args.tx_channel:04x} {cmd3}')

adapter.stop()
