using System;
using System.IO.Pipes;
using Debug = UnityEngine.Debug;
using System.Net.Sockets;
using Sock = System.Net.Sockets.Socket;
using System.Net;
using System.Linq;

public abstract class ICommunicator {
    public abstract byte[] Recv(int size);
    public abstract void Send(byte[] data);

    public int ReceiveSize() { 
        return (int)Serializer.FromBytes<long>(Recv(8));
    }

    public byte[] ReceiveUnit() {
        return Recv(ReceiveSize());
    }

    public IEntry ReceiveEntry() {
        var got = ReceiveUnit();
        string typename = Serializer.FromBytes<string>(got);
        string message = Serializer.FromBytes<string>(ReceiveUnit());
        object data = Serializer.FromBytes(typename, ReceiveUnit());
        if(typename == "") return null;
        Type entryType = typeof(Entry<>).MakeGenericType(data.GetType());
        return (IEntry)Activator.CreateInstance(entryType, message, data);
    }

    public DataList ReceiveDataList() {
        DataList dataList = new();
        int headerCount = ReceiveSize();
        for(int i=0;i<headerCount;i++) {
            dataList.AddHeader(ReceiveEntry());
        }
        int contentCount = ReceiveSize();
        for(int i=0;i<contentCount;i++) {
            dataList.AddContent(ReceiveEntry());
        }
        return dataList;
    }

    public void SendSize(int size) {
        Send(Serializer.ToBytes(size));
    }

    public void SendUnit(byte[] data) {
        SendSize(data.Length);
        Send(data);
    }
    
    public void SendEntry(IEntry entry) {
        SendUnit(Serializer.ToBytes(entry.GetTypeName()));
        SendUnit(Serializer.ToBytes(entry.GetMessage()));
        SendUnit(Serializer.ToBytes(entry.GetData()));
    }

    public void SendDataList(DataList datalist) {
        if (datalist == null) {
            Debug.Log("No datalist was given to communicator");
            return;
        }
        SendSize(datalist.GetHeaders().Count);
        datalist.GetHeaders().ForEach(SendEntry);
        SendSize(datalist.GetContent().Count);
        datalist.GetContent().ForEach(SendEntry);
    }
}

public class Pipe : ICommunicator {
    private volatile NamedPipeClientStream out_pipe;
    private volatile NamedPipeClientStream in_pipe;

    public Pipe(string in_name, string out_name) {
        in_pipe = new(".", in_name, PipeDirection.In);
        out_pipe = new(".", out_name, PipeDirection.Out);
        Debug.Log($"Pipe created at {in_name} and {out_name}");
    }

    public void Connect() {
        Debug.Log($"Trying to connect");
        in_pipe.Connect();
        out_pipe.Connect();
        Debug.Log("Successfully Connected!");
    }

    public void Disconnect() {
        in_pipe.Close();
        out_pipe.Close();
        Debug.Log("Successfully Closed!");
    }

    public override byte[] Recv(int size) {
        byte[] bytes = new byte[size];
        int totalReceived = 0;

        while (totalReceived < size) {
            int received = in_pipe.Read(bytes, totalReceived, size - totalReceived);
            totalReceived += received;
        }
        return bytes;
    }

    public override void Send(byte[] data) {
        out_pipe.Write(data, 0, data.Length);
    }
}


public class Socket : ICommunicator {
    private Sock socket;
    public bool working;

    public Socket(Sock socket=null, (string,int)? address=null) {
        if (socket != null) {
            this.socket = socket;
        } else if(address != null) {
            this.socket = PatientlyConnect(address.Value);
        } else {
            Debug.Log("Must provide a socket or an address");
            return;
        }
        working = true;
    }

    private Sock PatientlyConnect((string host,int port) address) {
        var clientSocket = new Sock(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        Debug.Log($"Trying to connect to {IPAddress.Parse(address.host)}:{address.port}");
        while(true) {
            try {
                clientSocket.Connect(IPAddress.Parse(address.host), address.port);
                return clientSocket;
            } catch (Exception) {
                Debug.Log($"Connection refused, trying again");
                System.Threading.Thread.Sleep(200);
            }
        }
    }

    public void Disconnect() {
        if(!working) return;
        socket.Close();
        working = false;
    }
    
    public override byte[] Recv(int size) {
        byte[] receivedData = new byte[size];
        int receivedTotal = 0;
        while (receivedTotal < size) {
            int receivedBytes = socket.Receive(receivedData, receivedTotal, Math.Min(1024, size - receivedTotal), SocketFlags.None);
            if (receivedBytes == 0) throw new InvalidOperationException("Connection closed prematurely");
            receivedTotal += receivedBytes;
        }
        return receivedData;

    }

    public override void Send(byte[] data) {
        socket.Send(data);
    }
}