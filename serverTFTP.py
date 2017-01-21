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
MAX_SIZE = 1024

HOST = 'localhost'
PORT = int(sys.argv[1])
PATH = sys.argv[2]


class tftpSender:
    def __init__(self, file, client, sock):
        self.file = file
        self.client = client
        self.sock = sock
        self.blockNumber = 1
        self.data = self.file.read(512)
        self.packet = ""

    def transmit(self):
        self.sock.sendto(struct.pack("!HH%ds" % len(self.data), DATA, self.blockNumber, self.data), self.client)

    def ack(self, blockNumber):
        if blockNumber == self.blockNumber:
            print("Klient potwierdzil paczke: " + str(self.blockNumber))
            if len(self.data) < 512:
                return True
            else:
                self.data = self.file.read(512)
                self.blockNumber += 1

    def transmitFile(self):
        self.transmit()
        while True:
            try:
                self.packet, client = self.sock.recvfrom(MAX_SIZE)
            except socket.timeout:
                self.transmit()
                continue
            if client != self.client:
                continue
            opcode = struct.unpack("!H", self.packet[0:2])[0]
            if opcode == ACK:
                if self.ack(struct.unpack("!H", self.packet[2:4])[0]):
                    break
                self.transmit()


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('localhost', PORT))
sock.settimeout(0.1)

wait = 1

while True:
    try:
        while True:
            if wait == 1:
                print("Oczekuje klienta...")
                wait = 2
            packet, client = sock.recvfrom(MAX_SIZE)
            opcode = struct.unpack("!H", packet[0:2])[0]
            if opcode == RRQ:
                mode = packet[packet[2:].index("\0") + 3:-1].lower()
                if mode[1:-1] == "octet":
                    break

        print("Klient poprosil o plik: " + PATH + packet[2:packet[2:].index("\0") + 2])
        try:
            theFile = open(PATH + packet[2:packet[2:].index("\0") + 2], "r")
            print("Rozpoczynam wysylanie...")
            send = tftpSender(theFile, client, sock)
            send.transmitFile()
            print("Gotowe!\n")
            wait = 1
        except IOError:
            print("Klient podal bledna nazwe pliku.\n");
            sock.sendto(struct.pack("!H%ds" % len("Invalid name."), ERROR, "Invalid name."), client)
    except socket.timeout:
        pass
