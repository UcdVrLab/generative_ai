using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Debug = UnityEngine.Debug;
using Unity;
using UnityEngine;

public class ServiceResolver {
    private List<IService> services;
    private List<Sender> senders;
    private Dictionary<string, (IInput<DataList> input,bool local)> serviceResolverDict;

    public ServiceResolver(List<IService> services, List<Sender> senders) {
        (this.services, this.senders) = (services, senders);
        serviceResolverDict = GenerateDict();
    }

    public Dictionary<string, (IInput<DataList>,bool)> GenerateDict() {
        return services.ToDictionary(s => s.GetServiceName(), s => (s.GetOutputAsInput(), true))
        .Concat(senders.SelectMany(sender => sender.peer.services.Select(serv => (serv, sender)))
                       .ToDictionary(p => p.serv, p => ((IInput<DataList>)p.sender.output, false)))
        .ToDictionary(p => p.Key, p => p.Value);
    }

    public (IInput<DataList> input, bool local) Resolve(string serviceName) {
        return serviceResolverDict.GetValueOrDefault(serviceName, (null, false));
    }
}

public class Children {
    private List<IService> services;
    private List<Sender> senders;
    private List<Receiver> receivers;

    public Children(List<IService> services, List<Sender> senders, List<Receiver> receivers) {
        (this.services,this.senders,this.receivers) = (services,senders,receivers);
    }

    public List<IProcessor> GetAll() {
        return new List<IProcessor>().Concat(services).Concat(senders).Concat(receivers).ToList();
    }

    public void StartAll() {
        GetAll().ForEach(p => p.Start());
    }

    public void EndAll() {
        senders.ForEach(s => {s.RequestTermination();s.ExternalTerminate();});
        services.ForEach(s => s.ExternalTerminate());
    }

    public bool JoinAll(int msTimeout) {
        return GetAll().All(p => p.Join(msTimeout));
    }
}

public class ServiceGenerator {
    public static IService GenerateService(string handlerName, Type serviceType, QueueStream handlerConfluence, ConfluenceDict confluenceDict) {
        if(typeof(IService).IsAssignableFrom(serviceType)) return FromService(serviceType, handlerName, handlerConfluence, confluenceDict);
        if(typeof(IWrapper).IsAssignableFrom(serviceType)) {
            var wrapper = GameObject.FindFirstObjectByType(serviceType) as IWrapper ?? throw new Exception($"Wrapper: '{serviceType}' was not attached to a gameobject");
            return FromWrapper(wrapper, handlerName, handlerConfluence, confluenceDict);
        } else throw new Exception($"Type: '{serviceType}' is not a known service type");
    }

    public static IService FromService(Type serviceType, string handlerName, QueueStream handlerConfluence, ConfluenceDict confluenceDict) {
        return CreateProcessor(serviceType, handlerName, serviceType.FullName, handlerConfluence, confluenceDict, LoopMode.THREADED);
    }

    public static IService FromWrapper(IWrapper wrapper, string handlerName, QueueStream handlerConfluence, ConfluenceDict confluenceDict) {
        var service = CreateProcessor(wrapper.WhichType(), handlerName, wrapper.GetType().FullName, handlerConfluence, confluenceDict, wrapper.GetLoopMode());
        wrapper.AttachProcessor(service);
        return service;
    }

    public static IService CreateProcessor(Type processorType, string handlerName, string className, QueueStream handlerConfluence, ConfluenceDict confluenceDict, LoopMode loopMode) {
        var stream = confluenceDict.ContainsKey(className) ? new Confluence(confluenceDict[className]) : new QueueStream();
        if (typeof(MultiTransformer).IsAssignableFrom(processorType)) {
            return (IService)Activator.CreateInstance(processorType, handlerName, className, new Rapid(handlerConfluence), stream, loopMode);
        } else if (typeof(Transformer).IsAssignableFrom(processorType)) {
            return (IService)Activator.CreateInstance(processorType, handlerName, className, handlerConfluence, stream, loopMode);
        } else if (typeof(Consumer).IsAssignableFrom(processorType)) {
            return (IService)Activator.CreateInstance(processorType, handlerName, className, stream, loopMode);
        } else if (typeof(Producer).IsAssignableFrom(processorType)) {
            return (IService)Activator.CreateInstance(processorType, handlerName, className, handlerConfluence, loopMode);
        } else {
            throw new Exception("Service is not an implemented type");
        }
    }
}


public class Handler : RoutingDLProcessor {
    private StateRules stateRules;
    private Children children;

    public Handler(Self self, List<Peer> peers, VirtualNetwork virtualNetwork) 
    : base(MakeName(self.name), null, null, LoopMode.UNITY) {
        stateRules = new(virtualNetwork);
        output = new QueueStream();
        var confluenceDict = stateRules.GenerateConfluenceDict();
        var services = self.usedServices.Select(s => ServiceGenerator.GenerateService(name, s, (QueueStream)output, confluenceDict)).ToList();
        var socketStreams = peers.Select(p => new SocketStream(p));
        var senders = socketStreams.Select(ss => new Sender(ss, new())).ToList();
        var receivers = socketStreams.Select(ss => new Receiver((QueueStream)output, ss)).ToList();
        ServiceResolver serviceResolver = new(services, senders);
        input = new Delta(s => serviceResolver.Resolve(s));
        children = new(services, senders, receivers);
    }

    public static string MakeName(string name) {
        return $"Handler({name})";
    }

    public override void Start() {
        children.StartAll();
        base.Start();
    }

    public override void InternalTerminate() {
        children.EndAll();
        if(children.JoinAll(2000)) {
            Debug.Log("Successfully terminated all threads, peacefully exiting");
        } else {
            Debug.Log("Failded to terminate all threads, forcefully exiting");
        }
        Debug.Break();
    }

    public override SingleLabelList Process(DataList datalist) {
        if (datalist == null) InternalTerminate();
        var state = datalist.GetState();
        Debug.Log($"{name} has received {datalist}");
        if(!state.IsValid()) {
            var producer = datalist.HeaderPopper<string>("producer")?.data ?? null;
            state = stateRules.Assign(producer);
            datalist.ChangeState(state);
        }
        SingleLabelList sll = new();
        if(state.complete) {
            var selected = datalist.GetSelected();
            var possible = stateRules.GetPotentialServices(state);
            if(selected.Count == 0) selected.AddRange(possible);
            if(selected.Contains("all")) {
                selected.AddRange(possible);
                selected.Remove("all");
            }
            possible.AddRange(stateRules.GetDefaultServices());
            selected.ForEach(s => {
                var newState = stateRules.Update(state, s);
                if(newState.IsValid()) sll.Add((datalist.ShallowCopy(newState, true), s));
                else Debug.Log($"State: {newState} was invalid, not sending to '{s}'");
            });
        } else {
            sll.Add((datalist, stateRules.GetCurrentService(state)));
        }
        return sll;
    }
}