from contextlib import contextmanager
import threading


class rwLock:
    def __init__(self):
        self.readers = 0
        self.rLock: threading.Lock = threading.Lock()
        self.wLock: threading.Lock = threading.Lock()

    def acquire_rLock(self):
        self.rLock.acquire()
        readers += 1
        if readers == 1:
            self.wLock.Lock()
        self.rLock.release()

    def release_rlock(self):
        self.rLock.acquire()
        assert self.readers > 0
        self.readers -= 1
        if self.readers == 0:
            self.wLock.release()
        self.rLock.release()

    def acquire_wLock(self):
        self.wLock.acquire()

    def release_wLock(self):
        self.wLock.release()

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
