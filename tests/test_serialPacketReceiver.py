from unittest import TestCase
from unittest.mock import *
from protoGrapher import SerialPacketReceiver, GraphDataWrapper, pack_bytes
from time import sleep
import logging
import threading

class MockPort:

    def __init__(self):
        logging.info("initializing mock port.")
        self.mock_queue = b''
        self.mock_delay_sec = 0

    def mock_delay(self):
        sleep(self.mock_delay_sec)

    def read(self):
        read_loop_counter = 0
        while True:
            self.mock_delay()
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
        self.receiver = SerialPacketReceiver("mock_name", 0xDEADBEEF,async=True)
        self.test_graph_wrapper = GraphDataWrapper()

    def get_proto_loop(self):
        while True:
            r = self.receiver.receive_loop()
            if r is not None:
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

    def test_async_receive(self):
        self.test_graph_wrapper.payload = [1, 2, 3, 4]
        test_bytes = self.test_graph_wrapper.get_proto_bytes()

        self.receiver.s.mock_queue += pack_bytes(test_bytes)

        return_graph_wrapper = self.receiver.get_wrapper_async(1.0)

        print(str(return_graph_wrapper))

        self.assertEqual(
            str(self.test_graph_wrapper),
            str(return_graph_wrapper))


    def test_async_laggy_serial(self):
        self.test_graph_wrapper.payload = [1, 2, 3, 4]
        test_bytes = self.test_graph_wrapper.get_proto_bytes()

        self.receiver.s.mock_queue += pack_bytes(test_bytes)
        self.receiver.s.mock_delay_sec=0.02
        return_graph_wrapper = self.receiver.get_wrapper_async()
        self.assertIsNone(
            return_graph_wrapper,
            "Nothing should be returned immidiatelly such mock delay"
        )
        return_graph_wrapper = self.receiver.get_wrapper_async(10)

        self.assertEqual(
            str(self.test_graph_wrapper),
            str(return_graph_wrapper),
            "graph wrapper not returned despite long timeout setting"
        )

    def test_long_message(self):
        self.test_graph_wrapper.payload = range(0, 4300)
        test_bytes = self.test_graph_wrapper.get_proto_bytes()

        self.receiver.s.mock_queue += pack_bytes(test_bytes)
        #self.receiver.s.mock_delay_sec=0.02
        return_graph_wrapper = self.receiver.get_wrapper_async()
        self.assertIsNone(
            return_graph_wrapper,
            "A lot of data is to be processed, I predict "
            "no immidiate results from worker thread"
        )
        return_graph_wrapper = self.receiver.get_wrapper_async(30)

        self.assertEqual(
            str(self.test_graph_wrapper),
            str(return_graph_wrapper),
            "graph wrapper not returned despite long timeout setting"
        )

    def test_kill_receiver(self):
        self.test_graph_wrapper.payload = range(0, 40)
        test_bytes = self.test_graph_wrapper.get_proto_bytes()

        self.receiver.s.mock_queue += pack_bytes(test_bytes)
        self.receiver.s.mock_delay_sec=0.1
        return_graph_wrapper = self.receiver.get_wrapper_async(1)
        self.assertIsNone(
            return_graph_wrapper,
            "Nothing should be returned so fast with such mock delay"
        )
        #now lets kill that object

        self.receiver.__del__()

        print(threading.enumerate())
        self.assertTrue(
            True
        )