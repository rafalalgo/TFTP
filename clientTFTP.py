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


class tftpDownloader:
    def __init__(self, host, filename):
        self.numer = 1
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
        self.msg = 0
        self.addr = 0
        self.file = ""
        self.kod = hashlib.md5()

    def requestDownloadFile(self):
        message = self.rrq + self.filename + self.empty + self.octet + self.empty
        self.sock.sendto(message, (self.host, self.port))
        self.sock.settimeout(0.1)
        self.receivePacket(message, 1)
        self.host = self.addr[0]
        self.port = int(self.addr[1])

    def check(self, out):
        text = struct.unpack('!HH', out[:4])
        
        if text[0] == DATA and text[1] == self.numer and len(out[4:]) < MAX_SIZE:
            self.kod.update(str(out[4:]))
            self.file += str(out[4:])
            return END
        elif text[0] == DATA and text[1] == self.numer and len(out[4:]) >= MAX_SIZE:
            self.kod.update(str(out[4:]))
            self.file += str(out[4:])
            return NEXT
        elif text[0] == DATA and text[1] == self.numer - 1:
            self.sock.sendto(str(struct.pack('!HH', ACK, text[1])), (self.host, self.port))
            return WRONG_NUMBER
        elif text[0] == DATA:
            return WRONG_NUMBER

    def receivePacket(self, last, tr):
        while True:
            try:
                self.msg, self.addr = self.sock.recvfrom(8 * MAX_SIZE)
                return
            except socket.timeout:
                if tr == 1:
                    self.sock.sendto(last, (self.host, self.port))
                else:
                    self.sock.sendto(str(struct.pack('!HH', ACK, self.numer - 1)), (self.host, self.port))
        self.msg = seld.addr = 0

    def start(self):
        self.requestDownloadFile()

        while True:
            k = self.check(self.msg)
            last = str(struct.pack('!HH', ACK, self.numer))

            if k == END:
                self.numer = (self.numer + 1) % 65536
                self.sock.sendto(last, (self.host, self.port))
                break

            if k == NEXT:
                self.sock.sendto(last, (self.host, self.port))
                self.receivePacket(last, 0)
                self.numer = (self.numer + 1) % 65536

            if k == WRONG_NUMBER:
                self.receivePacket(last, 0)

    def getCode(self):
        return self.kod.hexdigest()

    def getFile(self):
        return self.file


t = tftpDownloader(str(sys.argv[1]), str(sys.argv[2]))
t.start()
print(t.getFile())
print(t.getCode())
