using System;
using UnityEngine;

public interface IWrapper {
    Type WhichType();
    void AttachProcessor(IProcessor processor);
    LoopMode GetLoopMode();
}

public abstract class Wrapper<T,U> : MonoBehaviour, IWrapper {
    protected Processor<T,U> processor;
    [SerializeField] protected bool processorAttached = false;

    public abstract LoopMode GetLoopMode();

    public void AttachProcessor(IProcessor processor) {
        this.processor = processor as Processor<T,U>;
        processorAttached = true;
    }

    public Type WhichType() {
        if(typeof(T) == typeof(object)) return typeof(Producer);
        if(typeof(U) == typeof(object)) return typeof(Consumer);
        if(typeof(U) == typeof(DataList)) return typeof(Transformer);
        else return typeof(MultiTransformer);
    }
}

public abstract class EventWrapper<T,U> : Wrapper<T,U> {
    public override LoopMode GetLoopMode() { return LoopMode.EVENT; }

    public abstract bool ConditionsMet();
    public abstract U OnEvent(T t);

    void Update() {
        if(processorAttached && !processor.IsTerminated() && ConditionsMet()) processor.Single(OnEvent);
    }  
}

public abstract class UpdateWrapper<T,U> : Wrapper<T,U> {
    public override LoopMode GetLoopMode() { return LoopMode.UNITY; }

    public abstract U OnUpdate(T t);

    void Update() {
        if(processorAttached && !processor.IsTerminated()) processor.Single(OnUpdate);
    }
}