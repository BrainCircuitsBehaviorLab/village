import socket
from queue import Empty, Queue
from threading import Event, Thread


class NonBlockingSocketReceive:
    def __init__(self, sck):
        """s
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        """
        self._s = sck
        self._q = Queue()

        class PopulateQueue(Thread):
            def __init__(self, sck, queue):
                Thread.__init__(self)
                self.daemon = True
                self.socket = sck
                self.queue = queue
                self.event = Event()

            def run(self):
                try:
                    self.socket.settimeout(1.0)
                    data = None
                    while True:
                        if self.event.is_set():
                            break

                        if not self.socket:
                            break
                        try:
                            data = self.socket.recv(64)
                            if not data:
                                self.event.set()
                        except socket.timeout:
                            pass
                        if data:
                            self.queue.put(data)
                            data = None

                        self.event.wait(0.01)

                except OSError:
                    self.event.set()

        self._t = PopulateQueue(self._s, self._q)
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            return None

    def close(self):
        self._t.event.set()

    def is_alive(self):
        return self._t.is_alive()


class UnexpectedEndOfStream(Exception):
    pass
