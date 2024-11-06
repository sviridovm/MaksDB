# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: vector_db.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'vector_db.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0fvector_db.proto\x12\x08vectordb\"V\n\x0bInitRequest\x12\x0f\n\x07\x64\x62_path\x18\x01 \x01(\t\x12\x13\n\x0bvector_size\x18\x02 \x01(\x05\x12\x0e\n\x06metric\x18\x03 \x01(\t\x12\x11\n\tdest_path\x18\x04 \x01(\t\"/\n\x0cInitResponse\x12\x0e\n\x06status\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"!\n\x0eUpsertResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\"+\n\rQueryResponse\x12\x1a\n\x12matched_vector_ids\x18\x01 \x03(\x05\"2\n\rUpsertRequest\x12\x11\n\tvector_id\x18\x01 \x01(\x05\x12\x0e\n\x06vector\x18\x02 \x03(\x02\")\n\x0cQueryRequest\x12\x0e\n\x06vector\x18\x01 \x03(\x02\x12\t\n\x01n\x18\x02 \x01(\x05\x32\xcb\x01\n\x0fVectorDBService\x12\x35\n\x04Init\x12\x15.vectordb.InitRequest\x1a\x16.vectordb.InitResponse\x12\x41\n\x0cUpsertVector\x12\x17.vectordb.UpsertRequest\x1a\x18.vectordb.UpsertResponse\x12>\n\x0bQueryVector\x12\x16.vectordb.QueryRequest\x1a\x17.vectordb.QueryResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'vector_db_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_INITREQUEST']._serialized_start=29
  _globals['_INITREQUEST']._serialized_end=115
  _globals['_INITRESPONSE']._serialized_start=117
  _globals['_INITRESPONSE']._serialized_end=164
  _globals['_UPSERTRESPONSE']._serialized_start=166
  _globals['_UPSERTRESPONSE']._serialized_end=199
  _globals['_QUERYRESPONSE']._serialized_start=201
  _globals['_QUERYRESPONSE']._serialized_end=244
  _globals['_UPSERTREQUEST']._serialized_start=246
  _globals['_UPSERTREQUEST']._serialized_end=296
  _globals['_QUERYREQUEST']._serialized_start=298
  _globals['_QUERYREQUEST']._serialized_end=339
  _globals['_VECTORDBSERVICE']._serialized_start=342
  _globals['_VECTORDBSERVICE']._serialized_end=545
# @@protoc_insertion_point(module_scope)