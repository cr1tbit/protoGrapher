import logging

from protoGrapher import graphData_pb2 as pb
from json import dumps as format_dict


class GraphDataWrapper:

    def __init__(self, proto_packet=None, proto_object=None):
        self.packet_name = "undefined"
        self.packet_type = pb.T_UNKNOWN

        self.payload = []
        self.proto_version = 0
        self.meta = {}

        if proto_packet is not None:
            if type(proto_packet) in [bytes, bytearray]:
                self.parse_from_bytearray(proto_packet)
                return
            else:
                raise TypeError("expected type bytes, found "+str(type(proto_packet)))

        if proto_object is not None:
            if type(proto_object) is pb.graphData:
                self.parse_from_proto(proto_object)
                return
            else:
                raise TypeError("expected protobuf object, found "+str(type(proto_object)))
        else:
            logging.info("creating empty graph data wrapper object")
            self.parse_from_proto(pb.graphData())

    def __str__(self):
        return (
            "Graph data wrapper for packet: " +
            str(self.packet_name) +
            ", type '" + str(self.packet_type) + "'.\n" +
            str(len(self.payload)) + " payload samples, " +
            "graph metadata:\n" +
            format_dict(self.meta, indent=2, sort_keys=False)
        )

    def __getitem__(self, item):
        return self.meta[item]

    def __setitem__(self, key, value):
        self.meta[key] = value

    def parse_from_bytearray(self,packet):
        graph_proto = pb.graphData()
        graph_proto.ParseFromString(packet)
        self.parse_from_proto(graph_proto)

    def get_proto_bytes(self, int32_payload=False):
        g = pb.graphData()
        g.packetName = self.packet_name
        g.packetType = self.packet_type

        for v in self.payload:
            if int32_payload:
                g.payload_int32.append(v)
            else:
                g.payload.append(v)
        g.graphId = self.meta['id']

        g.graphXName = self.meta['x']['name']
        g.graphXUnit = self.meta['x']['unit']
        g.graphXSampleValue = self.meta['x']['sample_value']
        g.graphXSampleNo = self.meta['x']['sample_no']

        g.graphYName = self.meta['y']['name']
        g.graphYUnit = self.meta['y']['unit']

        g.payloadStartIndex = self.meta['payload']['start_index']
        g.payloadLen = self.meta['payload']['len']

        g.graphDataVersion = self.proto_version
        return g.SerializeToString()

    def attr_if_set(self,proto,key,default):
        if proto.HasField(key):
            return getattr(proto,key,default)
        return default

    def parse_from_proto(self,graph_proto: pb.graphData):
        self.packet_name = graph_proto.packetName
        self.packet_type = graph_proto.packetType

        [self.payload.append(n) for n in graph_proto.payload]
        [self.payload.append(n) for n in graph_proto.payload_int32]

        self.meta = {
            'id': self.attr_if_set(graph_proto,'graphId',0),
            'x': {
                'name': self.attr_if_set(graph_proto,'graphXName',"x axis"),
                'unit': self.attr_if_set(graph_proto,'graphXUnit',"u"),
                'sample_no': self.attr_if_set(graph_proto,'graphXSampleNo',len(self.payload)),
                'sample_value': self.attr_if_set(graph_proto,'graphXSampleValue',1.0),
                'range': 0  # calculated below, after other metadata is filled in
            },
            'y': {
                'name': self.attr_if_set(graph_proto,'graphYName',"x axis"),
                'unit': self.attr_if_set(graph_proto,'graphYUnit',"u")
            },
            'payload': {
                'start_index': self.attr_if_set(graph_proto,'payloadStartIndex',0),
                'len': self.attr_if_set(graph_proto,'payloadLen',len(self.payload))
            }
        }
        self.meta['x']['range'] =\
            self.meta['x']['sample_no'] * self.meta['x']['sample_value']
        self.proto_version = self.attr_if_set(graph_proto,'graphDataVersion',0)