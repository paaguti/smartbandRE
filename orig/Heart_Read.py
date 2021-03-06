import pygatt
import time
from random import *
import logging
from binascii import hexlify
adapter = pygatt.GATTToolBackend()

adapter.start()
def noti(handle, value):
    """
    handle -- integer, characteristic read handle the data was received on
    value -- bytearray, the data returned in the notification
    """
    value1=hexlify(value)
    print(value)
    print("Heart: %d BPM" % int(hexlify(value)[-2:],16))

while True:
    # mac = 'E8:77:6D:8B:09:96'
    mac = 'c3:44:7d:d8:c0:5d'
    # sid = 'c3e6fea2-e966-1000-8000-be99c223df6a'
    sid = '00001800-0000-1000-8000-00805f9b34fb'
    try:
        device = adapter.connect(mac, timeout=1, address_type=pygatt.BLEAddressType.random)
        device.subscribe(sid, callback=noti)
        break
    except pygatt.exceptions.NotConnectedError:
        print('Waiting...')

while True:
    adapter.sendline('char-write-req 0x0011 00')


    #finally:
adapter.stop()
print('Done')
