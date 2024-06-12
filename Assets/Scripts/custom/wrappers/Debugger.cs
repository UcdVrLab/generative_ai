using System.Collections.Concurrent;
using TMPro;
using UnityEngine;
using System.Linq;
using System.Collections.Generic;

namespace Wrappers.Core {
    public class Debugger : UpdateWrapper<DataList, object> {
        public TextMeshProUGUI text;
        public int NumberOfMessages = 5;
        private Buffer<string> buffer;

        void Start() {
            buffer = new(NumberOfMessages);
        }

        public override object OnUpdate(DataList dl) {
            buffer.LimitedEnqueue(dl.ContentGetter<string>(message: "log")?.data);
            UpdateUI();
            return null;
        }

        public void UpdateUI() {
            var new_text = buffer.Select(a => $">{a}").Aggregate((a,b) => $"{a}\n{b}");
            text.SetText(new_text);
        }
    }
}

class Buffer<T> : Queue<T> {
    public int Limit { get; set; }

    public Buffer(int limit) : base() { Limit = limit; }
    
    public void LimitedEnqueue(T obj) {
        Enqueue(obj);
        if(Count > Limit) Dequeue();
    }
}