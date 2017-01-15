#!/usr/bin/env python

import sys
import socket
import struct
import hashlib
import threading

EMPTY = 0
RRQ = 1
WRQ = 2
DATA = 3
ACK = 4
ERROR = 5
END = 10
WRONG_NUMBER = 20
NEXT = 30
MAX_SIZE = 1024

WAIT_FOR_RRQ = 1
WAIT_FOR_ACK = 2

HOST = 'localhost'

PATH = sys.argv[2]
PORT = int(sys.argv[1])


class tftpSender:
    def __init__(self, file, client, sock):
        self.file = file
        self.client = client
        self.sock = sock
        self.blockNumber = 1
        self.data = self.file.read(512)

    def transmit(self):
        self.sock.sendto(struct.pack("!HH%ds" % len(self.data), DATA, self.blockNumber, self.data), self.client)

    def ack(self, blockNumber):
        if blockNumber == self.blockNumber:
            if len(self.data) < 512:
                return True
            else:
                self.data = self.file.read(512)
                self.blockNumber += 1

    def isSameClient(self, client):
        return client == self.client


def waitForRRQ(sock):
    while True:
        packet, client = sock.recvfrom(MAX_SIZE)
        opcode = getOpcode(packet)
        if opcode == RRQ:
            mode = packet[packet[2:].index("\0") + 3:-1].lower()
            print(mode, "octet")
            if mode[1:-1] == "octet":
                break
    print("MAM")
    return client


def transmitFile(theFile, client, sock):
    transmitter = tftpSender(theFile, client, sock)
    sock.settimeout(2.0)
    transmitter.transmit()
    while True:
        try:
            packet, client = sock.recvfrom(MAX_SIZE)
            print(packet)
        except socket.timeout:
            transmitter.transmit()
            continue
        if not transmitter.isSameClient(client):
            continue
        opcode = getOpcode(packet)
        print(opcode, ACK)
        if opcode == ACK:
            if transmitter.ack(struct.unpack("!H", packet[2:4])[0]):
                break
            transmitter.transmit()


def getOpcode(packet):
    return struct.unpack("!H", packet[0:2])[0]


theFile = open(PATH, "r")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('localhost', PORT))
while True:
    client = waitForRRQ(sock)
    theFile.seek(0, 0)
    transmitFile(theFile, client, sock)
