using UnityEngine;
using Dummies;

namespace Wrappers.Core {
    public class Speaker : UpdateWrapper<DataList,object> {
        [SerializeField] AudioSource source;

        public override object OnUpdate(DataList dl) {
            source ??= gameObject.GetComponent<AudioSource>();
            source.PlayOneShot(dl.ContentPopper<Audio>()?.data.ToAudioClip());
            return null;
        }
    }
}