from queue import Queue, Empty
import socket
import threading


class TcpDataServer:
    def __init__(self, queue: Queue, host='0.0.0.0', port=1234):
        self.queue = queue
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket = None
        
        self.start_thread = threading.Thread(target=self._start)
        self.stop_event = threading.Event()
        
    def _start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            
            self.client_socket, addr = self.socket.accept()

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
        if self.start_thread.is_alive():
            self.stop()
        self.start_thread.start()

    def stop(self):
        if self.client_socket is None:
            self.socket.close()

        self.stop_event.set()
        self.start_thread.join()
        self.stop_event.clear()
        self.socket.close()

    def get_port(self):
        return self.port
