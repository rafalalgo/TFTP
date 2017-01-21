#!/usr/bin/env python

import sys
import socket
import struct
import hashlib

EMPTY = 0
RRQ = 1
WRQ = 2
DATA = 3
ACK = 4
ERROR = 5
END = 10
WRONG_NUMBER = 20
NEXT = 30
PORT = int(sys.argv[3])
MAX_SIZE = 512
WINDOWSIZE = int(sys.argv[4])


class tftpDownloader:
    def __init__(self, host, filename):
        self.numer = 0
        self.host = host
        self.port = PORT
        self.empty = str(struct.pack('!H', EMPTY))
        self.rrq = str(struct.pack('!H', RRQ))
        self.wrq = str(struct.pack('!H', WRQ))
        self.data = str(struct.pack('!H', DATA))
        self.ack = str(struct.pack('!H', ACK))
        self.error = str(struct.pack('!H', ERROR))
        self.filename = filename
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.octet = "octet"
        self.windowsize = "windowsize"
        self.packet = 0
        self.addr = 0
        self.file = ""
        self.kod = hashlib.md5()
        self.confirm = 0

    def receivePacket(self, last):
        while True:
            try:
                self.packet, self.addr = self.sock.recvfrom(8 * MAX_SIZE)
                return
            except socket.timeout:
                self.sock.sendto(last, (self.host, self.port))
        self.packet = seld.addr = 0

    def start(self):
        self.message = self.rrq + self.filename + self.empty + self.octet + self.empty + self.windowsize + self.empty + str(
            WINDOWSIZE) + self.empty
        self.sock.sendto(self.message, (self.host, self.port))
        self.sock.settimeout(0.1)
        self.receivePacket(self.message)
        self.host = self.addr[0]
        self.port = int(self.addr[1])

        while True:
            finish = 0
            error = 0
            text = struct.unpack('!HH', self.packet[:4])

            if text[0] == DATA and text[1] == self.numer + 1 and len(self.packet[4:]) < MAX_SIZE:
                self.kod.update(str(self.packet[4:]))
                self.file += str(self.packet[4:])
                self.numer += 1
                finish = 1
            elif text[0] == DATA and text[1] == self.numer + 1 and len(self.packet[4:]) >= MAX_SIZE:
                self.kod.update(str(self.packet[4:]))
                self.file += str(self.packet[4:])
                self.numer += 1
            elif text[0] == DATA and text[1] != self.numer + 1 and len(self.packet[4:]) == MAX_SIZE:
                last = str(struct.pack('!HH', ACK, self.numer))
                self.sock.sendto(last, (self.host, self.port))
                error = 1
            else:
                break

            if (self.numer - self.confirm) == WINDOWSIZE and error == 0:
                last = str(struct.pack('!HH', ACK, self.numer))
                self.sock.sendto(last, (self.host, self.port))

            if finish == 1:
                last = str(struct.pack('!HH', ACK, self.numer))
                self.sock.sendto(last, (self.host, self.port))
                break

            self.receivePacket(str(struct.pack('!HH', ACK, self.numer)))

    def getCode(self):
        return self.kod.hexdigest()

    def getFile(self):
        return self.file


t = tftpDownloader(str(sys.argv[1]), str(sys.argv[2]))
t.start()
print(t.getFile())
print(t.getCode())
