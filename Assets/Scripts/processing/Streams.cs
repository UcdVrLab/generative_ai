using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using System.Collections.Concurrent;
using System.Linq;

public interface IInput<T> { 
    public void Input(T t, bool block); 
}
public interface IOutput<T> { 
    public T Output(bool block);
}

public interface IStream<T> : IInput<T>, IOutput<T> {}

public class SingleLabelList : List<(DataList dataList,string name)> {}
public class MultiLabelList : List<(DataList dataList,List<string> names)> {}

public class Delta : IInput<SingleLabelList> {
    private Func<string, (IInput<DataList>,bool)> resolver;

    public Delta(Func<string, (IInput<DataList>,bool)> resolver) {
        this.resolver = resolver;
    }
    
    public void Input(SingleLabelList sll, bool block) {
        sll.ForEach(p => {
            var (input, local) = resolver.Invoke(p.name);
            p.dataList.GetState().complete = local;
            input?.Input(p.dataList, block);
        });
    }
}

public class Queue : BlockingCollection<DataList> {}

public class QueueStream : IStream<DataList> {
    private Queue queue = new();

    public QueueStream(Queue queue = null) {
        this.queue = queue ?? new();
    }

    public virtual void Input(DataList dl, bool block) {
        if(block) queue.Add(dl);
        else queue.TryAdd(dl);
    }

    public virtual DataList Output(bool block) {
        if(block) return queue.Take();
        bool took = queue.TryTake(out DataList dl);
        if(took) return dl;
        else throw new SkipExeception();
    }
}

public class SocketStream : IStream<DataList> {
    public Peer peer;

    public SocketStream(Peer peer) {
        this.peer = peer;
    }

    public void Input(DataList dl, bool block) {
        if(!block) throw new Exception("SocketStream must block");
        if(peer.CanSend()) peer.SendDataList(dl);
    }

    public DataList Output(bool block) {
        if(!block) throw new Exception("SocketStream must block");
        return peer.CanReceive() ? peer.ReceiveDataList() : null;
    }
}

public class NullStream : IStream<object> {
    public void Input(object t, bool block) { }
    public object Output(bool block) { return null; }
}

public class Rapid : IInput<MultiLabelList>, IOutput<DataList> {
    private QueueStream queueStream;

    public Rapid(QueueStream queueStream=null) {
        this.queueStream = queueStream ?? new();
    }

    public void Input(MultiLabelList mll, bool block) {
        mll.ForEach(p => {
            p.dataList.SetSelected(p.names);
            queueStream.Input(p.dataList, block);
        });
    }

    public DataList Output(bool block) {
        return queueStream.Output(block);
    }
}

public class Confluence : QueueStream {
    private Dictionary<int, Group> mainGrouplistDict;
    private Dictionary<int, Dictionary<int,int>> mainStateGroupDict;
    private Dictionary<int, Dictionary<int, DataList>> exampleDict;

    public Confluence(Dictionary<int, Group> confluenceDict, Queue queue=null) {
        mainGrouplistDict = confluenceDict;
        mainStateGroupDict = CreateMainStateGroupDict();
        exampleDict = CreateExampleDict();
    }

    private Dictionary<int, Dictionary<int,int>> CreateMainStateGroupDict() {
        return mainGrouplistDict.ToDictionary(
            pair => pair.Key,
            pair => pair.Value.SelectMany((list, i) => list.Select(s => new{ s, i }))
                              .ToDictionary(p => p.s, p => p.i)
        );
    }

    private Dictionary<int, Dictionary<int, DataList>> CreateExampleDict() {
        return mainGrouplistDict.ToDictionary(
            p => p.Key,
            p => p.Value.SelectMany(l => l).ToDictionary(s => s, _ => (DataList)null)
        );
    }

    private int DLToStateID(DataList dl) { return dl.GetPreviousState().id; }
    private int DLToGroupID(DataList dl) { return mainStateGroupDict[DLToMainID(dl)][DLToStateID(dl)]; }
    private int DLToMainID(DataList dl) { return dl.GetState().id; }
    private (int,int,int) DLToIDs(DataList dl) { return (DLToStateID(dl), DLToMainID(dl), DLToGroupID(dl)); }

    //code below is based on current datalist's ids
    private int mid,sid,gid;
    
    private List<DataList> GetGroupExamples() {
        return mainGrouplistDict[mid][gid].Select(s => exampleDict[mid][s]).ToList();
    }

    private bool GroupSatisfied() {
        return GetGroupExamples().All(dl => dl != null);
    }

    private DataList Merge() {
        var examples  = GetGroupExamples();
        DataList mergedDL = new();
        mergedDL.ChangeState(examples[0].GetState());
        mergedDL.SetPreviousState(gid); //gimmick
        examples.ForEach(e => {
            mergedDL.AddContent(e.GetContent());
            exampleDict[mid][DLToStateID(e)] = null;
        });
        return mergedDL;
    }

    private bool InsertDataList(DataList dl) {
        bool wasEmpty = exampleDict[mid][sid] == null;
        exampleDict[mid][sid] = dl;
        return wasEmpty;
    }

    public override void Input(DataList dl, bool block) {
        if(dl == null) {base.Input(dl, block); return;}
        (sid, mid, gid) = DLToIDs(dl);
        if(InsertDataList(dl) && GroupSatisfied()) base.Input(Merge(), block); 
    }
}