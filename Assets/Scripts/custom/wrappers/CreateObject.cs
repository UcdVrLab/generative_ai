using System;
using System.Collections.Generic;
using System.Threading;
using MeshProcess;
using UnityEngine;
using UnityEngine.XR;
using Valve.VR.InteractionSystem;
using Mesh = Dummies.Mesh;
using UnityEngine.XR.Interaction.Toolkit;

namespace Wrappers.Core {
    public class CreateObject : UpdateWrapper<DataList, object> {
        public GameObject prefab;
        public XRGrabInteractable Xrgrab;

        public override object OnUpdate(DataList dl) {
            var meshEntry = dl.ContentGetter<Dummies.Mesh>();
            var mesh = meshEntry?.data;
            var material = dl.ContentGetter<string>(message: "material")?.data;
            var sizeBytes = dl.ContentGetter<byte[]>(message: "size")?.data;
            var size = sizeBytes != null ? BitConverter.ToSingle(sizeBytes, 0) : 1.0f; // Default size is 1.0 if not specified

            // Print material and size received to console for debugging
            Debug.Log($"Material received: {material}");
            Debug.Log($"Size received: {size}");

            if (mesh == null) {
                CreateFailedObject();
                return null;
            }

            var obj = CreateGameObject(mesh, material ?? "normal", size);
            obj.name = meshEntry.message;

            var syncCtx = System.Threading.SynchronizationContext.Current;
            new System.Threading.Thread(() => ComputeVHACD(obj, mesh, syncCtx)).Start();

            return null;
        }

        private GameObject CreateGameObject(Dummies.Mesh mesh, string material, float size) {
            var obj = Instantiate(prefab, gameObject.transform);
            var mr = obj.GetComponent<MeshRenderer>();
            Shader shader;

            if (material.Equals("normal"))
                shader = Shader.Find("Shader Graphs/Normal");
            else if (material.Equals("metallic"))
                shader = Shader.Find("Shader Graphs/Metallic");
            else {
                var components = material.Split('-');
                shader = Shader.Find("Shader Graphs/Glowing");
            }

            mr.material = new Material(shader);
            obj.GetComponent<Rigidbody>().isKinematic = true;
            obj.GetComponent<MeshFilter>().mesh = mesh.ToUnityMesh(); // Convert custom mesh to Unity mesh

            // Apply scaling based on the size parameter
            obj.transform.localScale = size * Vector3.one;

            Debug.Log("Vertex counts: " + obj.GetComponent<MeshFilter>().mesh.vertexCount);

            TimerController.instance.EndTimer();
            return obj;
        }

        private void ComputeVHACD(GameObject obj, Dummies.Mesh mesh, System.Threading.SynchronizationContext main) {
            var convexHulls = AsyncVHACD.GenerateConvexMeshes(mesh);
            main.Post(_ => UpdateColliders(obj, convexHulls), null);
        }

        private void UpdateColliders(GameObject obj, List<Dummies.Mesh> convexHulls) {
            convexHulls.ForEach(h => {
                var collider = obj.AddComponent<MeshCollider>();
                collider.sharedMesh = h.ToUnityMesh(); // Convert custom mesh to Unity mesh for collider
                collider.convex = true;
            });

            obj.GetComponent<Rigidbody>().isKinematic = false;
            obj.AddComponent<XRGrabInteractable>();
            obj.GetComponent<XRGrabInteractable>().useDynamicAttach = true;
        }

        private void CreateFailedObject() {
            var obj = Instantiate(prefab, gameObject.transform);
            obj.name = "Failed Object";
            TimerController.instance.EndTimer();

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
