import time
import win32pipe, win32file
from socket import socket, AF_INET, SOCK_STREAM 
import socket as soc
import threading
import os

from networking.serializer import Serializer, SerializationException
from datastructs.datalist import DataList, Entry

class Communicator:
    def recv(self, size): pass
    def send(self, data): pass

    def receive_size(self):
        return Serializer.from_bytes(int, self.recv(8)) 
    
    def receive_unit(self):
        return self.recv(self.receive_size())
    
    def receive_entry(self) -> Entry:
        typename = Serializer.from_bytes(str, self.receive_unit())
        message = Serializer.from_bytes(str, self.receive_unit())
        data = Serializer.from_bytes_by_name(typename, self.receive_unit())
        return Entry(message, data)

    def receive_datalist(self):
        datalist = DataList(headers=[self.receive_entry() for _ in range(self.receive_size())], 
                            content=[self.receive_entry() for _ in range(self.receive_size())])
        #datalist.add_header(Entry("python received time", time.time_ns()))
        return datalist

    def send_size(self, size):
        self.send(Serializer.to_bytes(size))
    
    def send_unit(self, data):
        self.send_size(len(data))
        self.send(data)

    def send_entry(self, entry: Entry):
        self.send_unit(Serializer.to_bytes(entry.typename))
        self.send_unit(Serializer.to_bytes(entry.message))
        self.send_unit(Serializer.to_bytes(entry.data))

    def send_datalist(self, datalist: DataList):
        if not datalist: 
            print("No datalist given to communicator")
            return
        #datalist.add_header(Entry("python sending time", time.time_ns()))
        self.send_size(len(datalist.headers))
        for entry in datalist.headers:
            self.send_entry(entry)
        self.send_size(len(datalist.content))
        for entry in datalist.content:
            self.send_entry(entry)

class Pipe(Communicator):
    def __init__(self, in_name, out_name):
        self.input_pipe = win32pipe.CreateNamedPipe(
            in_name,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
            win32pipe.PIPE_UNLIMITED_INSTANCES,
            0, 0, 0, None
        )

        self.output_pipe = win32pipe.CreateNamedPipe(
            out_name,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
            win32pipe.PIPE_UNLIMITED_INSTANCES,
            0, 0, 0, None
        )

        print(f"Pipe created at {in_name} and {out_name}")

    def connect(self):
        print("Waiting for a connection...")
        win32pipe.ConnectNamedPipe(self.input_pipe, None)
        win32pipe.ConnectNamedPipe(self.output_pipe, None)
        print("Pipe connected")
    
    def disconnect(self):
        win32pipe.DisconnectNamedPipe(self.input_pipe)
        win32pipe.DisconnectNamedPipe(self.output_pipe)
        print("Pipe disconnected")
    
    def recv(self, size):
        return win32file.ReadFile(self.input_pipe, size)[1]

    def send(self, size):
        win32file.WriteFile(self.output_pipe, Serializer.to_bytes(size))

Address = tuple[str, int]

class Socket(Communicator):
    def __init__(self, sock: socket = None, address: Address = None):
        if sock is not None:
            self.socket = sock
        elif address is not None:
            self.patiently_connect(address)
        self.working = True

    def patiently_connect(self, address: Address):
        print(f"Connecting to {address}")
        self.socket = socket(AF_INET, SOCK_STREAM)
        while True:
            try:
                try:
                    self.socket.connect(address)
                    break
                except ConnectionRefusedError:
                    print("Connection refused, retrying...")
                    time.sleep(0.2)
            except KeyboardInterrupt:
                print("KeyBoard Interrupt... Exiting.")
                os._exit(1)
            
    def send(self, data):
        if not self.working: return
        try:
            self.socket.sendall(data)
        except soc.error as e:
            print(f"{threading.current_thread().name} Error sending data: {e}")
            self.working = False
            pass

    def recv(self, size):
        if not self.working: return b''
        try:
            received_total = 0
            received_data = bytearray()
            while received_total < size:
                chunk = self.socket.recv(min(1024, size - received_total))
                if not chunk:
                    raise RuntimeError("Connection closed prematurely")
                received_data.extend(chunk)
                received_total += len(chunk)
            return bytes(received_data)
        except soc.error as e:
            print(f"{threading.current_thread().name} Error receiving data: {e}")
            self.working = False
            return b''
    
    def disconnect(self):
        if not self.working: return
        self.socket.close()
        self.working = False