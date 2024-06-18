using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using UnityEngine;
using Debug = UnityEngine.Debug;

public class State {
    public int id;
    public bool complete;

    public State(int? _id, bool _complete=false) {
        (id, complete) = (_id ?? -4, _complete);
    }

    public static State LOST = new(-1, true);
    public static State CONFUSED = new(-2, true);
    public static State ERROR = new(-3, true);
    public static State UNKNOWN = new(-4, true);
    public static State ORPHAN = new(-5, true);

    public bool IsValid() {
        return IsReal() || id == -5;
    }

    public bool IsReal() { return id >= 0; }

    public override string ToString() {
        return $"State({id},{complete})";
    }
}

public class Cycle {
    private List<int> values;
    private int cur;

    public Cycle(List<int> values) {
        this.values = values;
        cur = 0;
    }

    public void Incr() {
        cur = (cur + 1) % values.Count;
    }

    public int Get(bool incr = true) {
        int v = values[cur];
        if (incr) Incr();
        return v;
    }
}
public class Group : List<List<int>> {}

public class ConfluenceDict : Dictionary<string,Dictionary<int,Group>> {
    public override string ToString() {
        return string.Join("\n", this.Select(p => $"({p.Key} : {string.Join("\n", p.Value.Select(k => $"({k.Key} : [{string.Join(",", k.Value.Select(l => $"{string.Join(",", l)}"))}])"))})"));
    }
}

public class StateRules {
    public VirtualNetwork network;
    public Dictionary<string, Cycle> producerCycles;

    public StateRules(VirtualNetwork _network) {
        network = _network;
        producerCycles = GenerateProducerCycles();
    }

    public Dictionary<string,Cycle> GenerateProducerCycles() {
        var producers = network.GetProducers();
        Dictionary<string, List<int>> idDict = new();
        producers.ForEach(p => {
            idDict.TryAdd(p.name, new());
            idDict[p.name].Add(p.id);
        });
        return idDict.ToDictionary(p => p.Key, p => new Cycle(p.Value));
    }

    public State Assign(string producer) {
        if (producer == null) return State.ORPHAN;
        return new(producerCycles.GetValueOrDefault(producer)?.Get(), true);
    }

    public State Update(State state, string selected=null) {
        if(!state.complete) return state;
        if(!state.IsValid()) return State.ERROR;
        if(!state.IsReal()) {
            var node = network.nodes.Where(n => n.name.Equals(selected) && n.isDefault).FirstOrDefault();
            return node != default(VNNode) ? new(node.id) : State.ERROR;
        }
        if(!network.HasNode(state.id)) return State.ERROR;
        var neighbours = network.GetNeighbours(state.id);
        if(neighbours.Count == 1) return new(neighbours[0].id);
        if(selected==null) return State.CONFUSED;
        var choice = neighbours.Where(n => n.name.Equals(selected)).First();                 //neighbours
        choice ??= network.nodes.Where(n => n.isDefault && n.name.Equals(selected)).First(); //default nodes
        return choice == null ? State.LOST : new(choice.id);
    }

    public string GetCurrentService(State state) {
        if(!state.IsReal()) return null;
        return network.GetNode(state.id).name;
    }

    public List<string> GetPotentialServices(State state) {
        if(!state.IsReal()) return new();
        return network.GetNeighbours(state.id).Select(n => n.name).ToList();
    }

    public List<string> GetDefaultServices() {
        return network.nodes.Where(n => n.isDefault).Select(n => n.name).ToList();
    }

    public ConfluenceDict GenerateConfluenceDict() {
        ConfluenceDict cd = new();
        foreach(var n in network.GetConsumers()) {
            cd.TryAdd(n.name, new());
            cd[n.name][n.id] = new();
            foreach(var pn in network.GetPreNeighbours(n.id)) {
                var edge = network.edgeDict[(pn.id, n.id)];
                var list = cd[n.name][n.id].Find(l => edge.SameGroup(network.edgeDict[(l[0], n.id)].group));
                if(list == default(List<int>)) cd[n.name][n.id].Add(new(){ pn.id });
                else list.Add(pn.id);
            }
        }
        return cd;
    }
}
