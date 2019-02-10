import serial
import graphData_pb2 as pb
import time
import logging
from enum import Enum
from array import array
from matplotlib import pyplot



class SerialPacketReceiver:
    def __init__(self, ser_name = "/dev/ttyUSB1", ser_baud = 115200):
        self.s = serial.Serial(port = ser_name,baudrate = ser_baud)
        self.s.baudrate = ser_baud

        self.sequence_buffer = bytearray(0)
        self.sequence_len = 4
        self.start_sequence = b'\x02\x02\x02\x02'
        self.end_sequence = b'\x03\x03\x03\x03'

        self.is_parsing = False
        self.payload_buffer = bytearray(0)
        self.max_payload_len = 4096

    def get_char(self):
        c = self.s.read(1)
        self.append_sequence_buffer(c)
        return c

    def append_sequence_buffer(self,c):
        self.sequence_buffer += c
        if len(self.sequence_buffer) > self.sequence_len:
            self.sequence_buffer = self.sequence_buffer[1:]

    def check_sequence(self,sequence_list):
        return self.sequence_buffer == sequence_list

    def is_payload_size_valid(self, buffer):
        try:
            len_bytes = buffer[0:2]
            pbuf_bytes = buffer[2:]
            len_from_buffer =\
                int(len_bytes[0])*0xFF + int(len_bytes[1])
            if len_from_buffer == len(pbuf_bytes):
                return True
            else:
                logging.error("invalid packet length detected")
                logging.error("buffer len - " + str(len(pbuf_bytes)))
                logging.error("supposed len - " + str(len_from_buffer))
                return False
        except IndexError:
            logging.error("invalid byte buffer length - validation failed")
            return False

    def receive_loop(self):
        c = self.get_char()
        #print(c)
        if self.is_parsing:
            self.payload_buffer+=c
            if len(self.payload_buffer)>self.max_payload_len:
                logging.error("packet extended maximum size - discarding.")
                self.payload_buffer = bytearray(0)
                self.is_parsing = False

        if self.check_sequence(self.end_sequence):
            final_payload = self.payload_buffer[:-4]
            if self.is_payload_size_valid(final_payload):
                #todo - add pushing to some kind of queue
                return self.get_samples_from_packet(final_payload)
            else:
                print("lel")
            self.is_parsing = False

        if self.check_sequence(self.start_sequence):
            logging.info("starting sequence detected - parsing data begin")
            self.payload_buffer = bytearray(0)
            self.is_parsing = True

    def get_samples_from_packet(self, packet_bytestring):
        graph_msg = pb.graphData()
        samples = []
        try:
            graph_msg.ParseFromString(packet_bytestring[2:])
            for n in graph_msg.payload:
                samples.append(n)
        except Exception as e:
            print("error parsing proto because")
            print(e)
        print (graph_msg.packetName)
        return samples






if __name__ == "__main__":
    r = SerialPacketReceiver()
    while True:
        samples = r.receive_loop()
        if samples is not None:
            pyplot.clf()
            pyplot.plot(samples[1:])
            pyplot.ion()
            pyplot.show()
            pyplot.draw()
            pyplot.pause(0.001)
