using UnityEngine;

namespace Wrappers.Core {
    public class SendPrompt : EventWrapper<object, DataList> {
        [SerializeField] private string prompt;
        [SerializeField] private string additionalPrompt;
        [SerializeField] private int width = 512;
        [SerializeField] private int height = 512;
        [SerializeField] private bool send;

        public void Send() {
            send = true;
        }

        public override bool ConditionsMet() {
            bool result = send;
            send = false;
            return result;
        }

        public override DataList OnEvent(object t) {
            DataList dl = new();
            dl.AddContent<string>(new("prompt", prompt + " " + additionalPrompt));
            dl.AddContent<long>(new("width", width));
            dl.AddContent<long>(new("height", height));
            return dl;
        }
    }
}