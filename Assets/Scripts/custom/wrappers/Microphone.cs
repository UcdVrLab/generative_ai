using System.Linq;
using UnityEngine;
using Dummies;
using Mic = UnityEngine.Microphone;
using UnityEngine.XR;
using Valve.VR;


namespace Wrappers.Core {
    public class Microphone : UpdateWrapper<object, DataList> {
        [SerializeField] Material micMaterial;
        [SerializeField] AudioSource playback;
        [SerializeField] string[] devices = {};
        [SerializeField] int selectedDevice = 0; 

        private AudioClip m_audio;

        public override DataList OnUpdate(object t) {
            devices = Mic.devices;
            if(Input.GetKeyDown(KeyCode.Space)) {
                // Debug.Log("Start le record");
                m_audio = Mic.Start(Mic.devices[selectedDevice],false,20,44100);
                micMaterial.color = Color.green;
            }
            if(Input.GetKeyDown(KeyCode.A)) {
                micMaterial.color = Color.red;
                // Debug.Log("Stop le record");
                Mic.End(Mic.devices[selectedDevice]);
                // playback.PlayOneShot(m_audio);
                return new(content: new() { new Entry<Audio>("audio", new(m_audio)) });
            }
            throw new SkipExeception();
        }
    }
}