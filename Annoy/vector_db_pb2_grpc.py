# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import Annoy.vector_db_pb2 as vector__db__pb2

GRPC_GENERATED_VERSION = '1.67.1'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in vector_db_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class VectorDBServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Init = channel.unary_unary(
                '/vectordb.VectorDBService/Init',
                request_serializer=vector__db__pb2.InitRequest.SerializeToString,
                response_deserializer=vector__db__pb2.InitResponse.FromString,
                _registered_method=True)
        self.UpsertVector = channel.unary_unary(
                '/vectordb.VectorDBService/UpsertVector',
                request_serializer=vector__db__pb2.UpsertRequest.SerializeToString,
                response_deserializer=vector__db__pb2.UpsertResponse.FromString,
                _registered_method=True)
        self.QueryVector = channel.unary_unary(
                '/vectordb.VectorDBService/QueryVector',
                request_serializer=vector__db__pb2.QueryRequest.SerializeToString,
                response_deserializer=vector__db__pb2.QueryResponse.FromString,
                _registered_method=True)


class VectorDBServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Init(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpsertVector(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueryVector(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_VectorDBServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Init': grpc.unary_unary_rpc_method_handler(
                    servicer.Init,
                    request_deserializer=vector__db__pb2.InitRequest.FromString,
                    response_serializer=vector__db__pb2.InitResponse.SerializeToString,
            ),
            'UpsertVector': grpc.unary_unary_rpc_method_handler(
                    servicer.UpsertVector,
                    request_deserializer=vector__db__pb2.UpsertRequest.FromString,
                    response_serializer=vector__db__pb2.UpsertResponse.SerializeToString,
            ),
            'QueryVector': grpc.unary_unary_rpc_method_handler(
                    servicer.QueryVector,
                    request_deserializer=vector__db__pb2.QueryRequest.FromString,
                    response_serializer=vector__db__pb2.QueryResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'vectordb.VectorDBService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('vectordb.VectorDBService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class VectorDBService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Init(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/vectordb.VectorDBService/Init',
            vector__db__pb2.InitRequest.SerializeToString,
            vector__db__pb2.InitResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def UpsertVector(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/vectordb.VectorDBService/UpsertVector',
            vector__db__pb2.UpsertRequest.SerializeToString,
            vector__db__pb2.UpsertResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueryVector(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/vectordb.VectorDBService/QueryVector',
            vector__db__pb2.QueryRequest.SerializeToString,
            vector__db__pb2.QueryResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
