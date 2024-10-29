from contextlib import contextmanager
import threading


class rwLock:
    def __init__(self):
        self.readers = 0
        self.reader_lock: threading.Lock = threading.Lock()
        self.writer_lock: threading.Lock = threading.Lock()

    def acquire_rLock(self):
        self.reader_lock.acquire()
        readers += 1
        if readers == 1:
            self.writer_lock.Lock()
        self.reader_lock.release()

    def release_rlock(self):
        self.reader_lock.acquire()
        assert self.readers > 0
        self.readers -= 1
        if self.readers == 0:
            self.writer_lock.release()
        self.reader_lock.release()

    def acquire_wLock(self):
        self.writer_lock.acquire()

    def release_wLock(self):
        self.writer_lock.release()

    @contextmanager
    def reader_lock(self):
        try:
            self.acquire_rLock()
            yield
        finally:
            self.release_rlock()

    @contextmanager
    def writer_lock(self):
        try:
            self.acquire_wLock()
            yield
        finally:
            self.release_wLock()
