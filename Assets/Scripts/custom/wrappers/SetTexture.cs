using UnityEngine;
using Dummies;

namespace Wrappers.Core {
    public class SetTexture : UpdateWrapper<DataList,object> {
        [SerializeField] MeshRenderer meshRenderer;

        public override object OnUpdate(DataList dl) {
            if (meshRenderer != null) {
                Material material = meshRenderer.material;
                if (material != null) {
                    material.mainTexture = dl.ContentPopper<Image>()?.data.ToTexture();
                }
                else Debug.LogError("Material not found on the MeshRenderer!");
            } else Debug.LogError("MeshRenderer not found on the GameObject!");
            return null;
        }
    }
}