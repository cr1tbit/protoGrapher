from unittest import TestCase
from unittest.mock import *
from protoGrapher import SerialPacketReceiver, GraphDataWrapper, pack_bytes
from time import sleep
import logging


class MockPort:

    def __init__(self):
        logging.info("initializing mock port.")
        self.mock_queue = b''

    def read(self):
        read_loop_counter = 0
        while True:
            if len(self.mock_queue) > 0:
                return_byte = bytes(self.mock_queue[:1])
                self.mock_queue = bytes(self.mock_queue[1:])
                #print(return_byte)
                return return_byte
            else:
                sleep(0.1)
                read_loop_counter += 1
                if (read_loop_counter % 100) == 0:
                    logging.info("stuck in read wait for {n} seconds..."
                                 .format(n=read_loop_counter / 10))


class TestSerialPacketReceiver(TestCase):

    def get_mock_port(self,name,baud):
        return MockPort()

    @patch.object(SerialPacketReceiver, 'get_serial_port', get_mock_port)
    def setUp(self):
        logging.getLogger().setLevel(logging.INFO)
        self.receiver = SerialPacketReceiver("mock_name", 0xDEADBEEF)
        self.test_graph_wrapper = GraphDataWrapper()

    def get_proto_loop(self):
        while True:
            r = self.receiver.receive_loop()
            if r is not None:
                print(type(r))
                return r
    ######################
    #  TESTS START HERE  #
    ######################

    # synchronous methods:
    def test_basic_receive(self):
        self.test_graph_wrapper.payload = [1, 2, 3, 4]
        test_bytes = self.test_graph_wrapper.get_proto_bytes()

        self.receiver.s.mock_queue += pack_bytes(test_bytes)

        return_graph_wrapper = self.get_proto_loop()

        print(str(return_graph_wrapper))

        self.assertEqual(
            str(self.test_graph_wrapper),
            str(return_graph_wrapper))


