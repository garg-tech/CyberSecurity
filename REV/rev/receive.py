#!/usr/bin/env python3
import os
import sys

from scapy.all import *
from scapy.layers.inet import _IPOption_HDR, Ether


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
    ifs=get_if_list()
    iface=None
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

class IPOption_MRI(IPOption):
    name = "MRI"
    option = 31
    fields_desc = [ _IPOption_HDR,
                    FieldLenField("length", None, fmt="B",
                                  length_of="swids",
                                  adjust=lambda pkt,l:l+4),
                    ShortField("count", 0),
                    FieldListField("swids",
                                   [],
                                   IntField("", 0),
                                   length_from=lambda pkt:pkt.count*4) ]

TyPE_REV = 0x860

def handle_pkt(pkt):
    if Rev in pkt:
        pkt.show2()
    sys.stdout.flush()


def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface = ifaces[0]
    print("sniffing on %s" % iface)
    sys.stdout.flush()
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x))

if __name__ == '__main__':
    main()

