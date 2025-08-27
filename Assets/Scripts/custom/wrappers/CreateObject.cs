using System;
using System.Collections.Generic;
using System.Threading;
using MeshProcess;
using UnityEngine;
using UnityEngine.XR;
using Valve.VR.InteractionSystem;
using Mesh = Dummies.Mesh;
using UnityEngine.XR.Interaction.Toolkit;
using static Serializer;


namespace Wrappers.Core {
    

    /*
    Created by: Jeric Antony - 20/08/25
    Class: ObjectCreationData
    This class holds all the data required to instantiate an object in Unity anmd can be used fro MOG and regular object generation and provides a basis for expansion
    */
    [System.Serializable]
    public class ObjectCreationData
    {
        public Dummies.Mesh mesh;
        public string material;
        public float size;
        public Vector3 gridPosition; // This is the grid coordinate (i, j, k)
        public string name; // The object's name
    }


    public class CreateObject : UpdateWrapper<DataList, object>
    {
        public GameObject prefab;
        public XRGrabInteractable Xrgrab;

        public GridHandler gridHandler;

        private string setup_name = null;
        private long totalMOGObjects = -1;
        private long mogObjectsCount = 0;

        public void SetGridHandler(GridHandler handler)
        {
            gridHandler = handler;
        }

        void Awake()
        {
            if (gridHandler == null)
            {
                gridHandler = FindObjectOfType<GridHandler>();
            }
        }
        void Start()
        {
            if (gridHandler == null)
            {
                gridHandler = FindObjectOfType<GridHandler>();
            }
        }



        /*
        Edited by: Jeric Antony
        Modified: 20/08/25
        Changes: Integration of MOG objects into Unity, control messages differentiates between MOG and regular object generation. Calls generateGrid once MOG setup is complete
        */

        public override object OnUpdate(DataList dl) //2 paths to unity, mog comes to unity twice so need to evade object creation if not full information
        {
            //info
            totalMOGObjects = dl.ContentPopper<long>(message: "MOG_TOTAL_OBJECTS")?.data ?? totalMOGObjects;
            setup_name = dl.ContentPopper<string>(message: "MOG_START_BATCH")?.data ?? setup_name;

            Debug.Log($"Name received: {setup_name}");
            Debug.Log($"Total received: {totalMOGObjects}");

            var mesh_failed = dl.ContentPopper<string>(message: "MESH_FAILURE")?.data;
            if (mesh_failed != null)
            {
                mogObjectsCount++;
                Debug.Log($"ShapE result missing for {mesh_failed} context. Ignoring.");
            }


            //obj data
            var meshEntry = dl.ContentGetter<Dummies.Mesh>();
            var mesh = meshEntry?.data;
            var material = dl.ContentGetter<string>(message: "material")?.data;
            var sizeBytes = dl.ContentGetter<byte[]>(message: "size")?.data;
            var size = sizeBytes != null ? BitConverter.ToSingle(sizeBytes, 0) : 1.0f; // Default size is 1.0 if not specified
            var positionEntry = dl.ContentGetter<Vector3>();
            Vector3 position = positionEntry?.data ?? Vector3.zero;

            // Print material and size received to console for debugging
            Debug.Log($"Material received: {material}");
            Debug.Log($"Size received: {size}");
            Debug.Log($"Position received: {position}");


            //MOG ONLY - add to pending objects
            if (positionEntry != null && mesh != null)
            {
                mogObjectsCount++;
                ObjectCreationData newObj = new ObjectCreationData
                {
                    mesh = mesh,
                    material = material,
                    size = size,
                    gridPosition = position,
                    name = meshEntry.message
                };
                gridHandler?.AddPendingObjectData(newObj); //add to MOG ready list

            }

            //MOG - Finished Setup Name Received
            if (setup_name != null && totalMOGObjects == mogObjectsCount)
            {
                Debug.Log($"Going to Generate Grid after setup received");
                gridHandler?.GenerateGrid(setup_name);
                setup_name = null;
                totalMOGObjects = -1;
                mogObjectsCount = 0;
                return null; //generate grid handles the creation of objects
            }



            if (positionEntry == null && totalMOGObjects == -1 && mesh_failed == null) //only for reg objgen
            {
                Transform placement = gridHandler.GetGridParentTransform() ?? gameObject.transform; //gets the grid or parent script object
                Vector3 centerOffset = GetGridCenterOffset(gridHandler?.gridsize ?? 0, gridHandler?.spacing ?? 0f); //gets middle of grid layout or world center if no grid

                ObjectCreationData reg_obj = new ObjectCreationData
                {
                    mesh = mesh,
                    material = material ?? "normal",
                    size = size,
                    gridPosition = centerOffset,
                    name = meshEntry.message
                };

                var obj = CreateGameObject(reg_obj, placement, centerOffset);
                TimerController.instance.EndTimer();
            }


            return null;
        }


        /*
        - Made by Jeric Antony 20/08/25
        Gets the center of the current Grid to place regularly generated objects
        */
        public static Vector3 GetGridCenterOffset(int gridSize, float spacing)
        {
            return new Vector3(
                (gridSize - 1) * spacing / 2f,
                (gridSize - 1) * spacing / 2f,
                (gridSize - 1) * spacing / 2f
            );
        }


        /*
        Refactored by: Jeric Antony 20/08/25, Uses ObjectCreationData class and passes the parent and placement location separately to allow resuse
        */
        public GameObject CreateGameObject(ObjectCreationData data, Transform parentTransform, Vector3 finalLocalPosition)
        {
            var obj = Instantiate(prefab); // Instantiate the base prefab
            obj.transform.SetParent(parentTransform, false); // Set parent without maintaining world position
            obj.transform.localPosition = finalLocalPosition; // Set the final local position after grid calculations

            obj.name = data.name;
            obj.transform.localScale = data.size * Vector3.one;
            obj.transform.localRotation = Quaternion.Euler(270, 0, 0); // All objects are upright - Jeric Antony, simple fix based on testing of ShapE meshes

            var mr = obj.GetComponent<MeshRenderer>();
            Shader shader;

            if (data.material.Equals("normal"))
                shader = Shader.Find("Shader Graphs/Normal");
            else if (data.material.Equals("metallic"))
                shader = Shader.Find("Shader Graphs/Metallic");
            else
            {
                var components = data.material.Split('-');
                shader = Shader.Find("Shader Graphs/Glowing"); // Fallback for glowing or unknown
            }
            mr.material = new Material(shader);

            obj.GetComponent<Rigidbody>().isKinematic = true; // Start kinematic until colliders are ready
            obj.GetComponent<MeshFilter>().mesh = data.mesh.ToUnityMesh(); // Convert custom mesh to Unity mesh

            if (data.size > 5) //designated large object by OBJGEN, this block ensures no clipping of floor for upright rotations of large objects - Jeric Antony
            {
                //UnityEngine.Mesh unityMesh = obj.GetComponent<MeshFilter>().mesh;
                //float lowestLocalY = unityMesh.bounds.center.y - unityMesh.bounds.extents.y; //center - half of size
                obj.transform.localPosition = new Vector3(obj.transform.localPosition.x, 0f, obj.transform.localPosition.z);
                Bounds actualWorldBounds = mr.bounds;

                obj.transform.localPosition = new Vector3(
                    obj.transform.localPosition.x,
                    obj.transform.localPosition.y + (-actualWorldBounds.min.y),
                    obj.transform.localPosition.z
                );

            }


            Debug.Log("Vertex counts: " + obj.GetComponent<MeshFilter>().mesh.vertexCount);

            // Trigger VHACD on a separate thread, then update colliders on the main thread
            var syncCtx = System.Threading.SynchronizationContext.Current;
            new System.Threading.Thread(() => ComputeVHACD(obj, data.mesh, syncCtx)).Start();

            return obj;
        }

        private void ComputeVHACD(GameObject obj, Dummies.Mesh mesh, System.Threading.SynchronizationContext main)
        {
            var convexHulls = AsyncVHACD.GenerateConvexMeshes(mesh);
            main.Post(_ => UpdateColliders(obj, convexHulls), null);
        }

        private void UpdateColliders(GameObject obj, List<Dummies.Mesh> convexHulls)
        {
            convexHulls.ForEach(h =>
            {
                var collider = obj.AddComponent<MeshCollider>();
                collider.sharedMesh = h.ToUnityMesh(); // Convert custom mesh to Unity mesh for collider
                collider.convex = true;
            });

            obj.GetComponent<Rigidbody>().isKinematic = false;
            obj.AddComponent<XRGrabInteractable>();
            obj.GetComponent<XRGrabInteractable>().useDynamicAttach = true;
        }

        private void CreateFailedObject()
        {
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
