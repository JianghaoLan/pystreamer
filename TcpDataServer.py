from queue import Queue, Empty
import socket
import threading


class TcpDataServer:
    def __init__(self, queue: Queue, host='127.0.0.1', port=0, thread_name=None):
        self.queue = queue
        self.host = host
        self.port = port
        self.socket = None
        self.client_socket = None

        self.start_thread = threading.Thread(target=self._start, name=thread_name)
        self.stop_event = threading.Event()
        self.started = False
        
    def _start(self):
        try:
            self.client_socket, _ = self.socket.accept()

            while True:
                try:
                    data = self.queue.get(timeout=0.5)
                    self.client_socket.send(data)
                except Empty:
                    if self.stop_event.is_set():
                        return
                    continue
                except Exception as e:
                    self.queue.task_done()
                    raise e
                self.queue.task_done()
        except OSError:
            return
        finally:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None
        
    def start(self):
        if self.started:
            raise RuntimeError("TcpDataServer can only be start() once.")
        
        self.started = True
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        self.start_thread.start()

    def stop(self):
        self.socket.close()
        self.stop_event.set()
        self.start_thread.join()

    def get_port(self):
        return self.socket.getsockname()[1]
