using Debug = UnityEngine.Debug;
using System.Net.Sockets;
using Sock = System.Net.Sockets.Socket;
using System.Net;
using System.Collections.Generic;
using System.Threading;
using System.Linq;

public class Peer : ICommunicator {
    public Socket clientSocket;
    public Socket serverSocket;
    public string myName;
    public string peerName;
    public List<string> services;
    
    public Peer(Socket _clientSocket, Socket _serverSocket, string _myName, string _peerName) {
        (clientSocket, serverSocket, myName, peerName) = (_clientSocket, _serverSocket, _myName, _peerName);
    }   

    public override byte[] Recv(int size) {
        return serverSocket.Recv(size);
    }

    public override void Send(byte[] data) {
        clientSocket.Send(data);
    }

    public (string,string) Names() {
        return (myName, peerName);
    }
    public (string,string) ReversedNames() {
        return (peerName,myName);
    }
    public bool CanSend() {
        return clientSocket.working;
    }
    public bool CanReceive() {
        return serverSocket.working;
    }
    public bool IsWorking() {
        return CanSend() && CanReceive();
    }

    public void SetServices(List<string> services) {
        this.services = services;
    }
}

public class Server {
    public Sock socket;
    public List<Socket> clients = new();
    public Thread serverThread;
    
    public Server((string host,int port) addr, int maxConnections) {
        socket = new(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        IPEndPoint ep = new(IPAddress.Parse(addr.host), addr.port);
        socket.Bind(ep);
        socket.Listen(maxConnections);
        Debug.Log($"Server listening on port {addr.port}");
        serverThread = new(() => AcceptConnections(maxConnections));
        serverThread.Start();
    }

    private void AcceptConnections(int maxConnections) {
        int connections = 0;
        while (connections < maxConnections) {
            var client = socket.Accept();
            Debug.Log($"Accepted connection from {client.RemoteEndPoint}");
            connections++;
            clients.Add(new Socket(client));
        }
        Debug.Log("Max connections");
    }

    public void Disconnect() {
        clients.ForEach(c => c.Disconnect());
        socket.Close();
        Debug.Log("Server Ended");
    }
}

public class Peers {
    public static (Self, List<Peer>) GenerateP2PConnections(string mainName, PhysicalNetwork net) {
        PNNode main = net.nodes.FirstOrDefault(n => n.name.Equals(mainName));
        if (main ==  null) {
            Debug.Log($"Given handler name does not exist: {mainName}. Existing");
            Debug.Break();
        }
        var others = net.nodes.Where(n => !n.name.Equals(mainName));
        Server server = new((main.ip, main.port), others.Count());

        var outClients = others.Select(p => new Socket(address: (p.ip, p.port))).ToList(); 
        outClients.ForEach(c => c.SendUnit(Serializer.ToBytes(mainName)));

        server.serverThread.Join();
        var inClientNames = server.clients.Select(c => Serializer.FromBytes<string>(c.ReceiveUnit())).ToList();;
        Self self = new(mainName, main.packages.Select(p => new Package(p)).ToList());   
        return (self, others.Zip(outClients, (node, outClient) => {
            var inClient = server.clients[inClientNames.FindIndex(n => n.Equals(node.name))];
            return new Peer(outClient, inClient, mainName, node.name); 
        }).ToList());
    }
}