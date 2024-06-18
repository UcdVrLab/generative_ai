from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os

from networking.communicator import Communicator, Socket, Address
from networking.self import Self,Package

#defines endpoint A's relationship to endpoint B as both a server and client
class Peer(Communicator): 
    def __init__(self, client_socket: Socket, server_socket: Socket, my_name: str, peer_name: str):
        self.client_socket = client_socket
        self.server_socket = server_socket
        self.my_name = my_name
        self.peer_name = peer_name

    #Send data to server B acting as client A
    def send(self, data: bytes):
        self.client_socket.send(data)
    
    #Receive data from client B acting as server A
    def recv(self, size: int):
        return self.server_socket.recv(size)

    @property
    def names(self):
        return (self.my_name,self.peer_name)
    
    @property
    def reversed_names(self):
        return (self.peer_name,self.my_name)
    
    def can_send(self):
        return self.client_socket.working

    def can_receive(self):
        return self.server_socket.working
    
    def isWorking(self):
        return self.can_send() and self.can_receive()
    
    def set_services(self, services: list[str]):
        self.services = services
    
class Server:
    def __init__(self, addr: Address, max_connections: int):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.clients: list[Socket] = []
        self.socket.bind(('127.0.0.1', addr[1]))
        self.socket.listen()
        print(f"Server listening on port {addr[1]}")
        self.connection_thread = Thread(target=self.accept_connections, args=(max_connections,))
        self.connection_thread.start()

    def accept_connections(self, max_connections: int):
        connections = 0
        while connections < max_connections:
            client = self.socket.accept()
            print(f"Accepted connection from {client[1]}")
            connections += 1
            self.clients.append(Socket(sock=client[0]))
        print(f"Max connecions") 

    def disconnect(self):
        for s in self.clients: s.socket.close()
        self.socket.close()
        print("Server Ended")
    
def generate_P2P_connections(main_name: str, physical_network) -> tuple[Self, list[Peer]]:
    nodes = physical_network['nodes']
    for p in nodes:
        if p["name"] == main_name:
            ip = p['ip']
            port = p['port']
            package_names = p['packages']
            break
    else:
        print(f"Given handler name does not exist: {main_name}. Exiting")
        os._exit(0)

    main_addr = (ip, int(port))
    peers_and_names = [(p['name'], p) for p in nodes if p['name'] != main_name]
    peer_addrs = [(p['ip'], int(p['port'])) for _,p in peers_and_names]

    server = Server(main_addr, len(peer_addrs))
    out_clients = [Socket(address=a) for a in peer_addrs]
    for c in out_clients: c.send_unit(main_name.encode())
    server.connection_thread.join()
    client_names = [bytes.decode(c.receive_unit()) for c in server.clients]
    return (Self(main_name, [Package(p) for p in package_names]), 
            [Peer(  oc, 
                    next((c for c,cn in zip(server.clients, client_names) if cn == n), None), 
                    main_name, 
                    n) for oc,(n,p) in zip(out_clients, peers_and_names)])