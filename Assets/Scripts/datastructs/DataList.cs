using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Debug = UnityEngine.Debug;

public interface IEntry {
    public string GetTypeName();
    public string GetMessage();
    public object GetData();
    public bool IsTerminal(string target=null);
}

public class Entry<T> : IEntry {
    public string typename;
    public string message;
    public T data;

    public Entry(string message, T data) {
        this.message = message;
        this.data = data;
        typename = Serializer.TypeToName(data.GetType());
    }

    public static IEntry GetTerminal(string target=null) {
        var command = (target==null) ? new Command(CommandType.EXIT) : new DirectCommand(CommandType.EXIT, target); 
        return new Entry<Command>("terminate", command);
    }

    public object GetData() { return data; }
    public string GetMessage() { return message; }
    public string GetTypeName() { return typename; }

    public bool IsTerminal(string target=null) {
        bool isTerminal = (data is Command command) && (command.type == CommandType.EXIT);
        bool isForTarget = data is not DirectCommand dc || (dc.target == target);
        return isTerminal && isForTarget;
    }

    public override string ToString() {
        return $"({typename}, {message}, {data})";
    }
}

public class DataList {
    private List<IEntry> headers;
    private List<IEntry> content;

    public DataList(List<IEntry> headers=null, List<IEntry> content=null) {
        this.headers = headers ?? new();
        this.content = content ?? new();
    }
    public void AddHeaders(List<IEntry> headers) {
        this.headers.AddRange(headers);
    }
    public void AddContent(List<IEntry> content) {
        this.content.AddRange(content);
    }
    public void AddHeader<T>(Entry<T> header) {
        this.headers.Add(header);
    }
    public void AddContent<T>(Entry<T> content) {
        this.content.Add(content);
    }
    public void AddHeader(IEntry header) {
        this.headers.Add(header);
    }
    public void AddContent(IEntry content) {
        this.content.Add(content);
    }
    public List<IEntry> GetHeaders() {
        return headers;
    }
    public List<IEntry> GetContent() {
        return content;
    }
    public List<Entry<T>> GetContent<T>() {
        return content.Where(e => e.GetTypeName() == Serializer.TypeToName(typeof(T))).Select(e => (Entry<T>)e).ToList();
    }
    private Entry<T> Getter<T>(List<IEntry> list, string message=null) {
        Func<IEntry,bool> pred = (message==null) ? (e => e.GetTypeName() == Serializer.TypeToName(typeof(T))) : (e => e.GetMessage() == message); 
        return list.FirstOrDefault(pred) as Entry<T>;
    }
    private Entry<T> Popper<T>(List<IEntry> list, string message=null) {
        var entry = Getter<T>(list, message);
        if(entry != null) list.Remove(entry);
        return entry;
    }
    public Entry<T> ContentGetter<T>(string message=null) {return Getter<T>(content, message);}
    public Entry<T> HeaderGetter<T>(string message=null) {return Getter<T>(headers, message);}
    public Entry<T> ContentPopper<T>(string message=null) {return Popper<T>(content, message);}
    public Entry<T> HeaderPopper<T>(string message=null) {return Popper<T>(headers, message);}

    public State GetState() {
        return HeaderGetter<State>()?.data ?? State.UNKNOWN;
    }
    public State GetPreviousState() {
        return new((int?)(HeaderGetter<long>("previous state")?.data), true);
    }
    public void ChangeState(State newState) {
        var oldState = HeaderPopper<State>();
        HeaderPopper<long>("previous state");
        AddHeader<long>(new("previous state", oldState?.data.id ?? State.UNKNOWN.id));
        AddHeader<State>(new("current state", newState));
    }
    //AKA lying, not the best solution
    public void SetPreviousState(int id) {
        HeaderPopper<long>("previous state");
        AddHeader<long>(new("previous state", id));
    }

    public List<string> GetSelected() {
        return (HeaderGetter<string>("selected")?.data ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries).ToList();
    }

    public void SetSelected(List<string> selected) {
        HeaderPopper<string>("selected");
        AddHeader<string>(new("selected", string.Join(",", selected)));
    }

    public static DataList GetTerminal(List<string> targets = null) {
        return new DataList(headers: (targets??new() {null}).Select(t => Entry<object>.GetTerminal(t)).ToList());
    }

    public bool HasTerminalCommand(string target = null) {
        return headers.Any(h => h.IsTerminal(target));
    }

    public DataList ShallowCopy(State newState=null, bool clearSelected=false) {
        DataList copy = new(new(headers), new(content));
        if(newState != null) copy.ChangeState(newState);
        if(clearSelected) copy.HeaderPopper<string>("selected");
        return copy;
    }

    public override string ToString() {
        return $"[{string.Join(",",headers)}][{string.Join(",",content)}]";
    }
}

