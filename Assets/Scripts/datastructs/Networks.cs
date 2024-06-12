using System;
using System.Collections.Generic;
using System.Linq;
using Debug = UnityEngine.Debug;

[Serializable]
public class PNNode {
    public string name;
    public string ip;
    public int port;
    public List<string> packages;

    public override string ToString() {
        return $"(name: {name}, addr: {ip}:{port}, packages: [{string.Join(",", packages)}])";
    }
}

[Serializable]
public class PhysicalNetwork { 
    public List<PNNode> nodes; 

    public PNNode GetNode(string name) {
        return nodes.First(n => n.name==name);
    }

    public override string ToString() {
        return $"[{string.Join(",", nodes)}]";
    }
}

[Serializable]
public class VNNode {
    public int id;
    public string name; 
    public bool isDefault;

    public override string ToString() {
        return $"(id: {id}, name: {name}, default: {isDefault})";
    }
}

[Serializable]
public class VNEdge {
    public int a;
    public int b;
    public string type;
    public string group;

    public override string ToString() {
        return $"({a}->{b}, type: {type}, group: {group})";
    }

    public bool SameGroup(string otherGroup) {
        if((otherGroup ?? "").Equals("") || (group ?? "").Equals("")) return false;
        return otherGroup.Equals(group);
    }
}

[Serializable]
public class VirtualNetwork {
    public List<VNNode> nodes;
    public List<VNEdge> edges; 

    public override string ToString() {
        return $"(nodes: [{string.Join(",", nodes)}], edges: [{string.Join(",", edges)}])";
    }

    [NonSerialized] public Dictionary<int, VNNode> nodeDict = new();
    [NonSerialized] public Dictionary<(int,int), VNEdge> edgeDict= new();
    [NonSerialized] public Dictionary<int, List<int>> neighbourDict= new();
    [NonSerialized] public Dictionary<int, List<int>> reverseNeighbourDict= new();

    public void Setup() {
        nodes.ForEach(n => {nodeDict.Add(n.id, n); neighbourDict.Add(n.id, new()); reverseNeighbourDict.Add(n.id, new());});
        edges.ForEach(e => edgeDict.Add((e.a, e.b), e));
        nodes.ForEach(n => edges.ForEach(e => {if(n.id == e.a) neighbourDict[n.id].Add(e.b);}));
        nodes.ForEach(n => edges.ForEach(e => {if(n.id == e.b) reverseNeighbourDict[n.id].Add(e.a);}));
    }

    public List<VNNode> GetConsumers() {
        return reverseNeighbourDict.Where(p => p.Value.Count > 0).Select(p => nodeDict[p.Key]).ToList();
    }
    public List<VNNode> GetProducers() {
        return reverseNeighbourDict.Where(p => p.Value.Count == 0).Select(p => nodeDict[p.Key]).ToList();
    }
    public List<VNNode> GetNeighbours(int nodeID) {
        return neighbourDict[nodeID].Select(id => nodeDict[id]).ToList();
    }
    public List<VNNode> GetPreNeighbours(int nodeID) {
        return reverseNeighbourDict[nodeID].Select(id => nodeDict[id]).ToList();
    }
    public bool HasNode(int nodeID) {
        return nodeDict.ContainsKey(nodeID);
    }
    public VNNode GetNode(int nodeID) {
        return nodeDict[nodeID];
    }
}