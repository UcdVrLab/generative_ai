using System;
using System.Collections.Generic;
using Debug = UnityEngine.Debug;
using System.Linq;
using System.Text.RegularExpressions;

public interface IService : INameable,IProcessor{
    public static string MakeName(string handler, string service) {
        return $"Service({handler}:{service})";
    }

    public string GetServiceName() {
        return Regex.Match(GetName(), @"(.+?)\((.+?):(.+?)\)").Groups[3].Value;
    }

    public IInput<DataList> GetOutputAsInput() {
        return GetType().GetBaseclasses()
        .First(t => t.IsGenericType && t.GetGenericTypeDefinition() == typeof(Processor<,>))
        .GetField("output").GetValue(this) as IInput<DataList>;
    }
}

public class Transformer : DLProcessor, IService {
    public Transformer(string handlerName, string name, QueueStream input, QueueStream output, LoopMode loopMode) 
    : base(IService.MakeName(handlerName, name), input, output, loopMode) {}
}

public class MultiTransformer : LabellingDLProcessor, IService {
    public MultiTransformer(string handlerName, string name, Rapid input, QueueStream output, LoopMode loopMode) 
    : base(IService.MakeName(handlerName, name), input, output, loopMode) {}

    public override MultiLabelList Process(DataList t) {
        throw new NotImplementedException();
    }
}

public class Consumer : DLInputter<object>, IService {
    public Consumer(string handlerName, string name, QueueStream output, LoopMode loopMode) 
    : base(IService.MakeName(handlerName, name), new NullStream(), output, loopMode) {}

    public override object Process(DataList t) {
        throw new NotImplementedException();
    }
}

public class Producer : DLOutputter<object>, IService {
    public Producer(string handlerName, string name, QueueStream input, LoopMode loopMode) 
    : base(IService.MakeName(handlerName, name), input, new NullStream(), loopMode) {}

    public override DataList Process(object t) {
        throw new NotImplementedException();
    }

    public override void Give(DataList dl) {
        dl?.AddHeader<string>(new("producer", ((IService)this).GetServiceName()));
        base.Give(dl);
    }

    public override void ExternalTerminate() {
        terminated = true;
    }
}

public class Sender : DLProcessor {
    public Peer peer;
    public Sender(SocketStream input, QueueStream output) 
    : base(MakeName(input.peer.myName, input.peer.peerName), input, output, LoopMode.THREADED) {
        peer = input.peer;
    }

    public static string MakeName(string local, string remote) {
        return $"Sender({local}->{remote})";
    }

    public void RequestTermination() {
        List<string> targets = new() { $"Handler({peer.peerName})", Receiver.MakeName(peer.peerName, peer.myName)};
        ((QueueStream)output).Input(DataList.GetTerminal(targets), true);
    }
}

public class Receiver : DLProcessor {
    public Peer peer;
    public Receiver(QueueStream input, SocketStream output) 
    : base(MakeName(output.peer.myName, output.peer.peerName), input, output, LoopMode.THREADED) {
        peer = output.peer;
    }

    public static string MakeName(string local, string remote) {
        return $"Receiver({local}<-{remote})";
    }

    public override void InternalTerminate() { terminated = true; }
}