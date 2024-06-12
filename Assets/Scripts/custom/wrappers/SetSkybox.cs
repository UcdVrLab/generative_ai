using UnityEngine;
using Dummies;

namespace Wrappers.Core {
    public class SetSkybox : UpdateWrapper<DataList,object> {
        public override object OnUpdate(DataList dl) {
            Material skyboxMaterial = new(Shader.Find("Skybox/Panoramic")) {
                mainTexture = dl.ContentPopper<Image>()?.data.ToTexture()
            };
            RenderSettings.skybox = skyboxMaterial;
            return null;
        }
    }
}