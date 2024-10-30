import grpc
from concurrent import futures
import vector_db_pb2_grpc
import vector_db_pb2
from db_manager import ModalDBManager, DBManager
from google.rpc import code_pb2


class VectorDBService(vector_db_pb2_grpc.VectorDBServiceServicer):
    def __init__(self):
        self.db = None

    def Init(self, request, context):
        db_path = request.db_path

        vector_size = request.vector_size
        metric = request.metric
        dest_path = request.dest_path

        if not db_path:
            try:
                self.db = DBManager(vector_size=vector_size,
                                    metric=metric, dest_path=dest_path)
                return vector_db_pb2.InitResponse(code=code_pb2., message="")
            except Exception as e:
                return vector_db_pb2.InitResponse(status=False, message="Init Failed")

        try:
            self.db = DBManager(src_path=db_path)
            return vector_db_pb2.InitResponse(status=True, message="")
        except Exception as e:

            return vector_db_pb2.InitResponse(status=False, message="Src file does not exist")

    def UpsertVector(self, request, context):
        vec = request.vector
        id = request.vector_id

        if not self.db:
            return vector_db_pb2.UpsertResponse(code=grpc.)

        try:
            self.db.execute_upsert(id, vec)
        except Exception as e:
            return vector_db_pb2.UpsertResponse(success=False)

        return vector_db_pb2.UpsertResponse(success=True)

    def QueryVector(self, request, context):
        return super().QueryVector(request, context)
