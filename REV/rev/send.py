#!/usr/bin/env python3
import random
import socket
import time
import sys

from scapy.all import *

TYPE_REV = 0x0860
TYPE_IPV4 = 0x0800

# REV Header Definition
class Rev(Packet):
    fields_desc = [
        BitField("pktHash", 0, 32),
        BitField("VID", 0, 48),
        BitField("timestamp", 0, 48),
        BitField("tag", 0, 32),
        BitField("type", 0, 16),
    ]

bind_layers(Ether, Rev, type=TYPE_REV)
bind_layers(Rev, IP, type=TYPE_IPV4)

def get_if():
    iface = None
    for i in get_if_list():
        if "eth0" in i:
            iface = i
            break
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

def main():
    if len(sys.argv) < 3:
        print('Usage: send.py <destination> "<message>" <number_of_packets>')
        exit(1)
    elif len(sys.argv) == 3:
        num_packets = 1
    else:
        num_packets = int(sys.argv[3])
                          
    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()

    print(f"Sending {num_packets} packets on interface {iface} to {addr}")
    for i in range(num_packets):
        curr_time = int(time.time() * 1000)
        timestamp = curr_time & ((1 << 48) - 1)
        vid = random.randint(1, 2**48 - 1)

        pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff', type=TYPE_REV)
        pkt = pkt / Rev(VID=vid, timestamp=timestamp, type=TYPE_IPV4)
        pkt = pkt / IP(dst=addr) / TCP(dport=1234, sport=random.randint(49152, 65535)) / sys.argv[2]
        pkt.show2()
        sendp(pkt, iface=iface, verbose=False)

if __name__ == '__main__':
    main()

