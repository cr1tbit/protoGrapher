from unittest import TestCase
from protoGrapher import SerialPacketReceiver, GraphDataWrapper, pack_bytes, pb
import logging

logging.getLogger().setLevel(logging.INFO)
class TestGraphDataWrapper(TestCase):

    def test_stub_objects(self):
        in_wrapper = GraphDataWrapper()
        in_wrapper.packet_name = "empty packet"
        bytes = in_wrapper.get_proto_bytes()
        self.assertGreater(len(bytes),0,"Empty bytestring returned")
        out_wrapper = GraphDataWrapper(bytes)
        #out_wrapper.parse_from_bytearray()
        #print("in wrapper:\n" + str(in_wrapper))
        #print("out wrapper:\n" + str(out_wrapper))
        self.assertEqual(
            str(in_wrapper),
            str(out_wrapper),
        )

    def test_real_objects(self):
        in_wrapper = GraphDataWrapper()
        in_wrapper.packet_name = "test packet"
        in_wrapper.packet_type = pb.T_GENERIC_CPLT
        in_wrapper.payload = [1, 2, 3, 4]
        in_wrapper['x']['name'] = "number index"
        in_wrapper['x']['unit'] = "i"
        in_wrapper['x']['sample_no'] = 4
        in_wrapper['x']['sample_value'] = 2.0
        in_wrapper['x']['range'] = (
            in_wrapper['x']['sample_no'] *
            in_wrapper['x']['sample_value']
        )
        in_wrapper['y']['name'] = "number value"
        in_wrapper['y']['unit'] = "u"
        in_wrapper['payload']['start_index'] = 1
        in_wrapper['id'] = 100

        packet = in_wrapper.get_proto_bytes()
        self.assertGreater(len(packet), 0, "Empty bytestring returned")
        out_wrapper = GraphDataWrapper(proto_packet=packet)
        self.assertEqual(
            str(in_wrapper),
            str(out_wrapper),
        )

        packet = in_wrapper.get_proto_bytes()
        self.assertGreater(len(packet),0,"Empty bytestring returned")
        out_wrapper = GraphDataWrapper()
        out_wrapper.parse_from_bytearray(packet)
        self.assertEqual(
            str(in_wrapper),
            str(out_wrapper),
        )
