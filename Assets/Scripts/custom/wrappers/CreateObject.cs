using System.Collections.Generic;
using System.Threading;
using MeshProcess;
using UnityEngine;
using UnityEngine.XR;
using Valve.VR.InteractionSystem;
using Mesh = Dummies.Mesh;
using UnityEngine.XR.Interaction.Toolkit;

namespace Wrappers.Core {
    public class CreateObject : UpdateWrapper<DataList,object> {
        public GameObject prefab;
        public XRGrabInteractable Xrgrab;
        public override object OnUpdate(DataList dl) {
            var meshEntry = dl.ContentGetter<Mesh>();
            var mesh = meshEntry?.data;
            var material = dl.ContentGetter<string>(message: "material")?.data;
            if(mesh == null) {
                CreateFailedObject();
                return null;
            }
            var obj = CreateGameObject(mesh, material ?? "normal");
            obj.name = meshEntry.message;
            var syncCtx = SynchronizationContext.Current;
            new Thread(() => ComputeVHACD(obj, mesh, syncCtx)).Start();
            return null;
        }

        public void ComputeVHACD(GameObject obj, Mesh mesh, SynchronizationContext main) {
            var convexHulls = AsyncVHACD.GenerateConvexMeshes(mesh);
            main.Post(_ => UpdateColliders(obj, convexHulls), null);
        }

        private GameObject CreateGameObject(Mesh mesh, string material) {
            var obj = Instantiate(prefab, gameObject.transform);
            var mr = obj.GetComponent<MeshRenderer>();
            Shader shader;
            if(material.Equals("normal")) shader = Shader.Find("Shader Graphs/Normal");
            else if(material.Equals("metallic")) shader = Shader.Find("Shader Graphs/Metallic");
            else {
                var components = material.Split('-');
                if(components.Length <2 || !components[0].Equals("glowing")) shader = Shader.Find("Shader Graphs/Normal");
                else shader = Shader.Find("Shader Graphs/Glowing");
            }
            mr.material = new Material(shader);
            obj.GetComponent<Rigidbody>().isKinematic = true;
            obj.GetComponent<MeshFilter>().mesh = mesh.ToUnityMesh();
            obj.transform.localScale = 0.5f * Vector3.one;
            
            return obj;
        }

        private void UpdateColliders(GameObject obj, List<Mesh> convexHulls) {
            convexHulls.ForEach(h => {
                var collider = obj.AddComponent<MeshCollider>();
                collider.sharedMesh = h.ToUnityMesh();
                collider.convex = true;
            }); 
            obj.GetComponent<Rigidbody>().isKinematic = false;
            obj.AddComponent<XRGrabInteractable>();
            obj.GetComponent<XRGrabInteractable>().useDynamicAttach = true;
        }

        private void CreateFailedObject() {
            var obj = Instantiate(prefab, gameObject.transform);
            obj.name = "Failed Object";
            var prim = GameObject.CreatePrimitive(PrimitiveType.Cube);
            obj.GetComponent<MeshFilter>().mesh = prim.GetComponent<MeshFilter>().mesh;
            var collider = obj.AddComponent<BoxCollider>();
            var primCol = prim.GetComponent<BoxCollider>();
            collider.center = primCol.center;
            collider.size = primCol.size;
            Destroy(prim);
            obj.transform.localScale = 0.5f * Vector3.one;
        }
    }
}