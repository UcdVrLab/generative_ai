using System;
using System.Diagnostics;
using System.Threading;
using Debug = UnityEngine.Debug;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;

public enum LoopMode {
    EVENT,
    THREADED,
    UNITY
}

public static class LoopModeExtension {
    public static bool IsBlocking(this LoopMode loopMode) {
        return loopMode == LoopMode.THREADED;
    }
}

public class SkipExeception : Exception {}
public class StopExeception : Exception {}

public interface IProcessor {
    void Start();
    bool Join(int msTimeout);
    void ExternalTerminate();
}

public abstract class Processor<T,U> : IProcessor {
    private Thread thread;
    public LoopMode loopMode;
    public IInput<U> input;
    public IOutput<T> output;
    protected bool terminated = false;

    public Processor(IInput<U> input, IOutput<T> output, LoopMode loopMode) {
        (this.input, this.output, this.loopMode) = (input, output, loopMode);
        if(loopMode == LoopMode.THREADED){
            thread = new(Loop);
        }
    }

    public bool IsTerminated() { return terminated; }
    public bool IsBlocking() { return loopMode.IsBlocking(); }

    public abstract U Process(T t);

    public virtual T Take() { return output.Output(IsBlocking()); }
    public virtual void Give(U u) { input.Input(u, IsBlocking()); }

    public virtual void OnExeception(Exception e) {
        Debug.Log(e.StackTrace);
        Debug.Break();
    }

    public void Loop() {
        while(!IsTerminated()) {
            Single(Process);
        }
        OnTermination();
    }

    public void Single(Func<T,U> func) {
        try {
            Give(func(Take()));
        } catch (SkipExeception) {
        } catch (StopExeception) {
            terminated = true;
        } catch (Exception e) {
            Debug.LogException(e);
            Debug.Break();
        }
    }

    public virtual void Start() {
        if(loopMode == LoopMode.THREADED) thread.Start();
    }

    public bool Join(int msTimeout) {
        if(loopMode != LoopMode.THREADED) return true;
        thread.Join(msTimeout);
        return !thread.IsAlive;
    }
    
    public virtual void InternalTerminate() {
        throw new StopExeception();
    }

    public virtual void ExternalTerminate() {
        terminated = true;
        FeedOutputNull();
    }

    public void FeedOutputNull() {
        (output as IInput<DataList>)?.Input(null, IsBlocking());
    }

    protected virtual void OnTermination() {}
}

public interface INameable {
    string GetName();
}

public abstract class NamedProcessor<T,U> : Processor<T,U>, INameable {
    public string name;

    public NamedProcessor(string name, IInput<U> input, IOutput<T> output, LoopMode loopMode) : base(input, output, loopMode) {
        this.name = name;
    }

    public string GetName() { return name; }
}

public abstract class DLInputter<U> : NamedProcessor<DataList, U> {
    protected DLInputter(string name, IInput<U> input, IOutput<DataList> output, LoopMode loopMode) : base(name, input, output, loopMode) {}

    public override DataList Take() {
        var dl = base.Take();
        if(dl == null || dl.HasTerminalCommand(name)) InternalTerminate();
        return dl;
    }
}

public abstract class DLOutputter<T> : NamedProcessor<T, DataList> {
    protected DLOutputter(string name, IInput<DataList> input, IOutput<T> output, LoopMode loopMode) : base(name, input, output, loopMode) {}
}

public abstract class DLProcessor : DLInputter<DataList> {
    protected DLProcessor(string name, IInput<DataList> input, IOutput<DataList> output, LoopMode loopMode) : base(name, input, output, loopMode) {}

    public override DataList Process(DataList dl) { return dl; }
}

public abstract class RoutingDLProcessor : DLInputter<SingleLabelList> {
    protected RoutingDLProcessor(string name, IInput<SingleLabelList> input, IOutput<DataList> output, LoopMode loopMode) : base(name, input, output, loopMode) {}
}

public abstract class LabellingDLProcessor : DLInputter<MultiLabelList> {
    protected LabellingDLProcessor(string name, IInput<MultiLabelList> input, IOutput<DataList> output, LoopMode loopMode) : base(name, input, output, loopMode) {}
}