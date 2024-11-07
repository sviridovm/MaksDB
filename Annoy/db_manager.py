import time
import warnings
from vectordb.utils.rw_lock import rwLock
from enum import Enum
import logging
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
import threading
import numpy as np
from Annoy.vector_db import VectorDB
from Annoy.utils import Search, Entry


class DBManager:
    def __init__(self, index_file: str = None, **kwargs):
        if index_file:
            self.db = VectorDB(index_file)
        else:
            self.db(**kwargs)

        self.executor = ThreadPoolExecutor()
        # thread safe queue
        self.upsert_queue: queue.Queue[Entry] = queue.Queue()
        self.lock = rwLock()

        # thread that runs to rebuild the index
        self.rebuild_thread = threading.Thread(
            target=self._rebuild, daemon=True)
        self.rebuild_thread.start()

        # logger :frog:
        self.logger = logging.getLogger(self.__name__)
        logging.basicConfig(level=logging.info)
        self.logger.info('Started DBManager')

    def execute_upsert(self, vector_id: int, vector: np.ndarray):
        val = self.executor.submit(self.upsert_queue.put,
                                   Entry(vector_id, vector))
        self.logger.info(f'Queued Upsert for vec_id {vector_id}')
        return val

    def exceute_query(self, vector: np.ndarray, n: int):
        if n <= 0:
            raise ValueError(
                f'Cannot search for nearest {n} vectors, n must be greater than 0')

        self.logger.info(
            f'Submitted nearest {n} similarity search for {vector}')

        return self.executor.submit(self._query, vector, n)

    def _query(self, vector: np.ndarray, n: int):
        with self.lock.reader_lock():
            self.db.search(vector, n)

    def _commit_upsert_batch(self):
        if self.upsert_queue.empty():
            return

        with self.lock.writer_lock():
            # commit all buffered upserts
            for entry in self.upsert_queue:
                self.db.add_vector(entry.id, entry.vector)
                self.logger.info(f'Commited vec_id {entry.id} to the index')

            self.db.build_index()
            self.upsert_queue.clear()
            self.db.save_index()

    def _rebuild(self):
        while True:
            time.sleep(15)
            self._commit_upsert_batch()


class Mode(Enum):
    Read = 1
    Write = 2


class ModalDBManager:
    def __init__(self, index_file: str = None, **kwargs):
        if index_file:
            self.db = VectorDB(index_file)
        else:
            self.db(**kwargs)

        self.mode: Mode = Mode.Read
        self.executor = ThreadPoolExecutor()
        self.lock = threading.Lock()

        self.read_queue = queue.Queue()
        self.write_queue = queue.Queue()

    def set_mode_read(self):
        if self.mode == Mode.Read:
            return

        self.executor.shutdown(wait=True)
        self.mode = Mode.Read
        self.db.build_index()
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.executor.map(self._reads_ops, self.read_queue)
        with self.read_queue.mutex:
            self.read_queue.clear()

    def set_mode_write(self):
        if self.mode == Mode.Write:
            return

        self.executor.shutdown(wait=True)
        self.mode = Mode.Write
        # Cannot write concurrently yet :eyes:
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        with self.executor:
            futures = [self.executor.map(self._write_ops, self.write_queue)]

            # wait for all previous writes to complete
            for future in as_completed(futures):
                pass

        with self.write_queue.mutex:
            self.write_queue.clear()

        self.db.save_index()

    # TODO: REFACTOR

    def _write_ops(self, entry: Entry):
        """Wrappers for thread pool map function"""
        if entry.id == -1:
            self.execute_delete()
        else:
            self.execute_upsert(self, entry.id, entry.vector)

    def _reads_ops(self, search: Search):
        """Wrappers for thread pool map function"""
        self.execute_query(search.vector, search.n)

    def execute_upsert(self, vector_id: int, vector: np.ndarray):
        # check id is not in the thinng

        if self.Mode == Mode.Read:
            self.executor.submit(self.write_queue.put,
                                 Entry(vector_id, vector))
            warnings.warn(
                'Attempting write operation during read mode. Operation will block until mode change')
            return

        with self.executor:
            self.executor.submit(
                self.upsert_queue.put, (vector_id, vector))

    def execute_query(self, vector: np.ndarray, n: int):
        if n <= 0:
            raise ValueError(
                f'Cannot search for nearest {n} vectors, n must be greater than 0')

        # could add an optimization where you are able to execute searches in write mode, if no writes have been executed
        # why tho
        if self.Mode == Mode.Write:
            self.executor.submit(self.read_queue.put, (vector, n))
            warnings.warn(
                'Attempting read operation during write mode. Operation will block until mode change')
            return

        return self.executor.submit(self.db.search, vector, n)

    def execute_delete(self):
        if self.Mode == Mode.Write:
            self.executor.submit(self.write_queue.put,
                                 Entry(-1, []))
            warnings.warn(
                'Attempting read operation during write mode. Operation will block until mode change')
            return

        return self.executor.submit(self.db.delete())


# def retry(retries: int = 3):
#     retries_left: int = retries

#     def decorator(func: function):
#         def inner(*args, **kwargs):
#             while retries_left > 0:
#                 try:
#                     return func(*args, **kwargs)
#                 except Exception as e:
#                     print(e)
#                     retries_left -= 1
#             raise Exception(
#                 f'Function {func.__name__} failed to execute after {retries} retries')
#         return inner
#     return decorator
