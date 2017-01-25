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
    def __init__(self, file, client, sock, windowsize):
        self.file = file
        self.client = client
        self.sock = sock
        self.packet = ""
        self.windowsize = int(windowsize)
        self.confirm = 0

    def load(self):
        self.data = list()
        temp = self.file.read(512)
        ind = 1
        while len(temp) > 0:
            self.data.append((ind, temp))
            temp = self.file.read(512)
            ind += 1
        self.data = sorted(self.data)
        self.data.insert(0, (0, 0))

    def transmit(self):
        for i in range(self.confirm + 1, min(self.confirm + 1 + self.windowsize, len(self.data))):
            self.sock.sendto(struct.pack("!HH%ds" % len(self.data[i][1]), DATA, i, self.data[i][1]), self.client)

    def ack(self, blockNumber):
        if blockNumber >= 1:
            print("Klient potwierdzil paczke: " + str(blockNumber))
            if len(self.data[blockNumber][1]) < 512:
                self.confirm = blockNumber
                return True
            else:
                self.confirm = blockNumber

    def transmitFile(self):
        self.load()
        self.transmit()
        while True:
            while True:
                try:
                    self.packet, client = self.sock.recvfrom(MAX_SIZE)
                    break
                except socket.timeout:
                    continue
            if client != self.client:
                continue
            opcode = struct.unpack("!H", self.packet[0:2])[0]
            if opcode == ACK:
                if self.ack(struct.unpack("!H", self.packet[2:4])[0]):
                    break
                self.transmit()
            if self.confirm == len(self.data) - 1:
                break


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
                from_mode = packet[packet[2:].index("\0") + 3:]
                from_mode = from_mode[1:]
                from_window = from_mode[from_mode[2:].index("\0") + 3:]
                from_window = from_window[1:]
                from_size = from_window[from_window[2:].index("\0") + 3:]
                from_size = from_size[1:]
                windowsize = from_size[:from_size.index("\0")]
                if from_mode[0:5] == "octet":
                    break

        print("Klient poprosil o plik: " + PATH + packet[2:packet[2:].index("\0") + 2])
        print("Klient zaproponowal system windowsize: " + windowsize)
        try:
            theFile = open(PATH + packet[2:packet[2:].index("\0") + 2], "r")
            print("Rozpoczynam wysylanie...")
            send = tftpSender(theFile, client, sock, windowsize)
            send.transmitFile()
            print("Gotowe!\n")
            wait = 1
        except IOError:
            print("Klient podal bledna nazwe pliku.\n");
            sock.sendto(struct.pack("!H%ds" % len("Invalid name."), ERROR, "Invalid name."), client)
    except socket.timeout:
        pass
