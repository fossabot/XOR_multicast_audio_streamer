####################################
# this controls way the software runs
########################################

import sys
import zlib
import pyaudio
import socket
import struct
import base64
import hashlib

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

from pip._vendor.urllib3.connectionpool import xrange

# for generating the XOR password
def ran(length):
    import random
    import string
    random = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(length)])
    return random

def Streamer():
    multicast_group = ('224.0.0.3', 10000)

    # Create the datagram socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # stops the packets passing out of the local network
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    ping = 0
    passd = bytes(ran(64).encode())
    # Open a file
    fo = open("pass", "wb")
    fo.write(passd)
    fo.close
    try:
        # Send data to the multicast group
        print(sys.stderr, 'sending')
        sent = sock.sendto(passd, multicast_group)

        # Look for responses from all recipients
        while True:
            if ping == 0:
                print(sys.stderr, 'waiting to receive')
                try:
                    data, server = sock.recvfrom(16)
                except socket.timeout:
                    print(sys.stderr, 'timed out, no more responses')
                    break
                else:
                    print(sys.stderr, 'received "%s" from %s' % (data, server))
                ping = 1
            else:

                p = pyaudio.PyAudio()

                stream = p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)

                print("* streaming")

                frames = []

                while True:
                    data = stream.read(CHUNK)
                    crc = zlib.crc32(data)
                    #data = xorcrypt(data, passd)
                    data = zlib.compress(data, 9) + "::" + crc
                    sent = sock.sendto(data, multicast_group)

    finally:
        print(sys.stderr, 'closing socket')
        sock.close()


def Reciver():
    multicast_group = '224.0.0.3'
    server_address = ('', 10000)

    # Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to the server address
    sock.bind(server_address)
    # Tell the operating system to add the socket to the multicast group
    # on all interfaces.
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    # Receive/respond loop

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    fo = open("pass", "r+")
    passd = fo.read()
    fo.close
    while True:
        print('\nwaiting to receive message')
        data, address = sock.recvfrom(1024)
        data = zlib.decompress(data)
        #data = xorcrypt(data, passd)
        data, packetcrc = data.split("::")
        crc = zlib.crc32(packetcrc)
        if crc == packetcrc:
            if packetcrc != '':
                stream.write(data)
            print(sys.stderr, 'received %s bytes from %s' % (len(data), address))
            print(sys.stderr, data)

        print(sys.stderr, 'sending acknowledgement to', address)
        sock.sendto('ack', address)

    stream.stop_stream()
    stream.close()

    p.terminate()


# runs the application
# Iteration over all arguments:
arg = sys.argv
if arg == "r":
    Reciver()
elif arg == "sr":
    Streamer()
else:
    print("didn't run the application correctly")
    exit()

