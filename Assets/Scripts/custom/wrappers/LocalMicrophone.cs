using System.Linq;
using UnityEngine;
using Dummies;
using Mic = UnityEngine.Microphone;
using UnityEngine.XR;
using Valve.VR;


/* Old Version using SteamVR you can inspire microphone.cs to do it */


namespace Wrappers.Core {
    public class LocalMicrophone : UpdateWrapper<object, DataList> {
        
        private SteamVR_Action_Boolean localMic = SteamVR_Actions.default_LocalMIC;
        private AudioClip m_audio;

        public override DataList OnUpdate(object t) {
            if(KeyDown()) {
                m_audio = Mic.Start(Mic.devices[0],false,20,44100);
            }
            if(KeyUp()) {
                Mic.End(Mic.devices[0]);
                return new(content: new() { new Entry<Audio>("audio", new(m_audio)) });
            }
            throw new SkipExeception();
        }

        private bool KeyDown() {
            if(XRSettings.enabled) {
                return localMic.GetStateDown(SteamVR_Input_Sources.Any);
            } else {
                return Input.GetKeyDown(KeyCode.V);
            }
        }

        private bool KeyPressed() {
            if(XRSettings.enabled) {
                return localMic.GetState(SteamVR_Input_Sources.Any);
            } else {
                return Input.GetKey(KeyCode.V);
            }
        }

        private bool KeyUp() { 
            if(XRSettings.enabled) {
                return localMic.GetStateUp(SteamVR_Input_Sources.Any);
            } else {
                return Input.GetKeyUp(KeyCode.V);
            }
        }
    }
}

