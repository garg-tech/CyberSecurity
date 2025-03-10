#!/usr/bin/env python3
import sys
import time
import threading
import queue
from scapy.all import *
from scapy.layers.inet import IP, Ether
import zlib
import argparse, os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../utils/'))
from switch_utils import load_topology

# Constants
TYPE_IPV4 = 0x0800
TYPE_REV = 0x0860

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

# Path Keys
path_keys = [0xa1b2c3d4, 0xe5f6a7b8, 0xc9d1e2f3, 0xa4b5c6d7, 0xe8f9a1b2, 0xc3d4e5f6, 0xe2f1a9b8,  0xa7b8c9d1, 0xe2f3a4b5, 0xc6d7e8f9, 0xa9b8c7d6, 0xe5f4a3b2, 0xc1d9e8f7, 0xa6b5c4d3, 0xa1b2c3d4, 0xe5f6a7b8, 0xc9d1e2f3, 0xa4b5c6d7, 0xe8f9a1b2, 0xc3d4e5f6, 0xe2f1a9b8,  0xa7b8c9d1, 0xe2f3a4b5, 0xc6d7e8f9, 0xa9b8c7d6, 0xe5f4a3b2, 0xc1d9e8f7, 0xa6b5c4d3, 0xa1b2c3d4, 0xe5f6a7b8]

# Shared queue for packets
source_queue = queue.Queue()
dest_queue = queue.Queue()

# Lock for shared resources
lock = threading.Lock()

# Global variables
matched_packets = {}
num_switches = 0
total_time = 0
packet_count = 0

def pack_data(data):
    """Pack data into bytes."""
    format_string = ">"
    for num in data:
        if num.bit_length() <= 16:
            format_string += "H"
        elif num.bit_length() <= 32:
            format_string += "I"
        elif num.bit_length() <= 64:
            format_string += "Q"
        else:
            raise ValueError(f"Value {num} is too large to pack!")
    return struct.pack(format_string, *data)

def calculate_crc32(packet_data):
    """Calculate the CRC32 hash for given packet data."""
    return zlib.crc32(packet_data)

def printGrpcError(e):
    print("gRPC Error: ", e.details())
    status_code = e.code()
    print ("(%s)" % status_code.name)
    # detail about sys.exc_info - https://docs.python.org/2/library/sys.html#sys.exc_info
    traceback = sys.exc_info()[2]
    print ("[%s:%s]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))

def process_source_packets(source):
    """Handle packets from the source switch."""
    global matched_packets
    while True:
        packetin = source.PacketIn()
        if packetin.WhichOneof('update') == 'packet':
            payload = packetin.packet.payload
            pktHash = int((payload[14:18]).hex(), 16)
            VID = int((payload[18:24]).hex(), 16)
            Timestamp = int((payload[24:30]).hex(), 16)
            with lock:
                matched_packets[VID] = {"pktHash": pktHash, "Timestamp": Timestamp}
                source_queue.put(VID)

def process_dest_packets(dest):
    """Handle packets from the destination switch."""
    global matched_packets, total_time, packet_count
    while True:
        packetin = dest.PacketIn()
        if packetin.WhichOneof('update') == 'packet':
            payload = packetin.packet.payload
            VID = int((payload[18:24]).hex(), 16)
            Tag = int((payload[30:34]).hex(), 16)
            with lock:
                if VID in matched_packets:
                    data = matched_packets.pop(VID)
                    pktHash = data["pktHash"]
                    Timestamp = data["Timestamp"]
                    tag = None
                    for i in range(num_switches - 2):
                        if i == 0:
                            packet_data = [pktHash, path_keys[i]]
                        else:
                            packet_data = [pktHash, tag, path_keys[i]]
                        packet_data_bytes = pack_data(packet_data)
                        tag = calculate_crc32(packet_data_bytes)
                    curr_time = int(time.time() * 1000)
                    time_taken = curr_time - Timestamp
                    if tag == Tag:
                        print(f"Rule Enforcement Verified! Time Taken: {time_taken} ms")
                    else:
                        print(f"Rule Enforcement Compromised! Time Taken: {time_taken} ms")
                    total_time += time_taken
                    packet_count += 1

def main(topo_file_path):
    global total_time, packet_count, num_switches
    try:
        # Load topology and identify switches
        switches, mn_topo = load_topology(topo_file_path)
        source, dest = None, None
        num_switches = len(switches)
        for bmv2_switch in switches.values():
            if bmv2_switch.name == 's1':
                source = bmv2_switch
            elif bmv2_switch.name == f's{num_switches}':
                dest = bmv2_switch
            bmv2_switch.MasterArbitrationUpdate()
            print(f"Established as controller for {bmv2_switch.name}")
        
        if not source or not dest:
            print("Source or Destination switch not found in the topology.")
            return

        # Start threads for processing packets
        source_thread = threading.Thread(target=process_source_packets, args=(source,))
        dest_thread = threading.Thread(target=process_dest_packets, args=(dest,))
        source_thread.start()
        dest_thread.start()

        # Wait for user to exit
        while True:
            time.sleep(10)
            if packet_count > 0:
                avg_time = total_time / packet_count
                print(f"Average Time for Verification: {avg_time:.2f} ms")
    
    except KeyboardInterrupt:
        print("Exiting controller...")
        # Add cleanup logic
        if source_thread.is_alive():
            source_thread.join(timeout=1)
        if dest_thread.is_alive():
            dest_thread.join(timeout=1)
        sys.exit(0)

    except grpc.RpcError as e:
        printGrpcError(e)

# Entry Point
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Controller for REV')
    parser.add_argument('--topo', help='Topology file', type=str, action='store', required=True)
    args = parser.parse_args()
    
    if not os.path.exists(args.topo):
        print(f"Topology file {args.topo} does not exist!")
        sys.exit(1)
    
    main(args.topo)

