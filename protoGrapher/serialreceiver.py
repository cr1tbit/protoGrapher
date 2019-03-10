import serial
import logging
from matplotlib import pyplot
from threading import Thread
from queue import Queue, Empty
from time import sleep

from protoGrapher.graphDataWrapper import GraphDataWrapper

logger = logging.getLogger('protoGrapher')

def pack_bytes(bytestring):
    return bytes(
        b'\x02\x02\x02\x02' +
        len(bytestring).to_bytes(2, byteorder='big') +
        bytestring +
        b'\x03\x03\x03\x03'
    )

class SerialPacketReceiver:
    def __init__(self, ser_name="/dev/ttyUSB1", ser_baud=460800,async=False):
        self.s = self.get_serial_port(ser_name, ser_baud)
        self.s.timeout = 1

        self.sequence_buffer = bytearray(0)
        self.sequence_len = 4
        self.start_sequence = b'\x02\x02\x02\x02'
        self.end_sequence = b'\x03\x03\x03\x03'

        self.is_parsing = False
        self.payload_buffer = bytearray(0)
        self.max_payload_len = 50000

        #threading stuff
        self.kill_order = False
        self.receive_thread = Thread(
            target=self.receive_worker,
            args=[],
            daemon=True,
            name="SerialReceiver-Thread"
        )
        self.receive_thread.daemon = True
        self.wrapper_queue = Queue()
        if async:
            self.receive_thread.start()

    def __del__(self):
        self.kill_order = True
        sleep(0.001) # yield thread for a bit
        for i in range(10):
            if not self.receive_thread.is_alive():
                logging.critical("thread killed.")
                return
            sleep(0.1)
        logging.critical("couldn't terminate workier thread... Bailing out.")

    def get_serial_port(self, name, baud):
        return serial.Serial(port=name, baudrate=baud)

    def get_char(self,timeout=None):
        self.s.timeout=timeout
        c = self.s.read()
        self.append_sequence_buffer(c)
        return c

    def append_sequence_buffer(self,c):
        self.sequence_buffer += c
        if len(self.sequence_buffer) > self.sequence_len:
            self.sequence_buffer = self.sequence_buffer[1:]

    def check_sequence(self, sequence_list):
        return self.sequence_buffer == sequence_list

    def is_payload_size_valid(self, buffer):
        try:
            len_bytes = buffer[0:2]
            pbuf_bytes = buffer[2:]
            len_from_buffer =\
                int(len_bytes[0])*0x100 + int(len_bytes[1])
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

    def receive_loop(self,timeout = None):
        c = self.get_char(timeout)
        if c is None:
            return

        if self.is_parsing:
            self.counter+=1
            self.payload_buffer+=c
            if len(self.payload_buffer) > self.max_payload_len:
                logging.error("packet extended maximum size - discarding.")
                self.payload_buffer = bytearray(0)
                self.is_parsing = False

        if self.check_sequence(self.end_sequence):
            logging.debug("end sequence detected!")
            self.sequence_buffer = bytearray(0)
            final_payload = self.payload_buffer[:-4]
            if self.is_payload_size_valid(final_payload):
                return GraphDataWrapper(final_payload[2:])
            else:
                logging.error("invalid payload size detected.")
            self.is_parsing = False

        if self.check_sequence(self.start_sequence):
            logging.info("starting sequence detected - parsing data begin")
            self.counter = 0
            self.sequence_buffer = bytearray(0)
            self.payload_buffer = bytearray(0)
            self.is_parsing = True

    #threading methods:
    def receive_worker(self):
        while True:
            wrapper = self.receive_loop(0.1)
            if wrapper is not None:
                self.wrapper_queue.put(wrapper)
            if self.kill_order:
                return

    def get_wrapper_async(self,timeout=0):
        try:
            return self.wrapper_queue.get(block=True, timeout=timeout)
        except Empty:
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format=('%(levelname)s:\t '
                                '%(filename)s'
                                '[%(lineno)d] in '
                                '%(funcName)s():\t '
                                '%(message)s')
                        )

    r = SerialPacketReceiver(ser_name='/dev/ttyUSB1', ser_baud=115200)
    wraps = [None, None, None]
    while True:
        wrappedData = r.receive_loop()
        if wrappedData is not None:
            wraps[wrappedData.meta['id']] = wrappedData
            pyplot.clf()
            for w in wraps:
                if w is not None:
                    pyplot.axis([0,256,0,10])
                    pyplot.xlabel("{n}[{u}]".format(
                        n=w.meta['x']['name'],
                        u=w.meta['x']['unit'])
                    )
                    pyplot.ylabel("{n}[{u}]".format(
                        n=w.meta['y']['name'],
                        u=w.meta['y']['unit'])
                    )
                    pyplot.xticks(range(0,w.meta['x']['range']+1,int(w.meta['x']['range']/8)))
                    #pyplot.axes.set_xscale(1,'linear')
                    pyplot.plot(w.payload[1:],label='test'+str(w.meta['id']))
            pyplot.legend()

            pyplot.ion()
            pyplot.show()
            pyplot.draw()
            pyplot.pause(0.1)
