using System;
using System.Collections.Generic;
using System.Threading;
using MeshProcess;
using UnityEngine;
using System.Linq; // Make sure this is included for .Any() and .Join()

/*
 * File: GridHandler.cs
 * Author: Jeric Antony
 * Created: 20/08/25
 * Description: Creates a grid for placing objects on that were created by CreateObject.cs, collates MOG objects together for instantaneous instantiation and provides a feature for reporting on the collsion between objects. 
*/

namespace Wrappers.Core
{

    //[System.Serializable] //place this back for manually entering of setup scene objects
    public class ObjectEntry //tracks objects that are currently in the scene to allow dynamic resizing and resetting of the grid
    {
        public GameObject prefab;
        public GameObject instantiatedGameObject;
        public Vector3 position;
        public Quaternion initialRotation;
    }

 
    public class GridHandler : MonoBehaviour
    {
        public int gridsize = 20;
        public float spacing = 1f;
        private float prevSpacing = -1f;
        private GameObject gridParent;

        public CreateObject createObject;


        public List<ObjectCreationData> pendingObjectData = new List<ObjectCreationData>();
        public List<ObjectEntry> objectEntries = new List<ObjectEntry>(); //list of object entries that can be instantiated
        private List<Vector3> occupiedPositions = new List<Vector3>(); //grid positions

        private SynchronizationContext _syncContext;
        void Awake()
        {
            _syncContext = SynchronizationContext.Current;

            if (gridParent == null)
            {
                gridParent = new GameObject("Setup Name");
            }

            createObject ??= FindObjectOfType<CreateObject>();
            createObject.SetGridHandler(this);
        }


        void Start()
        {
            GenerateGrid();
            Invoke("PrintCollisionReport", 0.1f);
        }

        public void AddPendingObjectData(ObjectCreationData data)
        {
            pendingObjectData.Add(data);
        }


        public Transform GetGridParentTransform()
        {
            return gridParent?.transform;
        }



        //Generates Grid for MOG pipeline    
        public void InstantiateAllPendingObjects()
        {
            WipeGrid();

            foreach (var objData in pendingObjectData)
            {
                Vector3 coord = objData.gridPosition;

                if (coord.x >= 0 && coord.x < gridsize && coord.y >= 0 && coord.y < gridsize && coord.z >= 0 && coord.z < gridsize)
                {
                    coord = IsPositionOccupied(coord, occupiedPositions); //tracks position collisions - can be changed to include size to stop clipping with large objects
                    occupiedPositions.Add(coord);

                    Vector3 finalLocalPosition = new Vector3(coord.x * spacing, coord.y * spacing, coord.z * spacing);

                    GameObject newSceneObject = createObject.CreateGameObject(objData, gridParent.transform, finalLocalPosition);

                    objectEntries.Add(new ObjectEntry
                    {
                        prefab = newSceneObject,
                        instantiatedGameObject = newSceneObject,
                        position = coord,
                        initialRotation = newSceneObject.transform.rotation,
                    }); //managment of runtime instantiated objects


                    //Collision Data gathering
                    CollisionData reporter = newSceneObject.GetComponent<CollisionData>();
                    if (reporter != null)
                    {
                        reporter.objectName = objData.name;
                    }
                }
                else
                {
                    Debug.LogWarning($"Warning: {objData.name} has invalid coordinates ({coord.x},{coord.y},{coord.z}). Skipping.");
                }
            }
            pendingObjectData.Clear();
            TimerController.instance.EndTimer(); //end timer as mog setup finished
        }


        //main function to update the grid
        public void GenerateGrid(string setup_name = "Setup Name")
        {

            if (pendingObjectData.Any()) //if mog is ready
            {
                gridParent.name = setup_name;
                InstantiateAllPendingObjects();
            }
            else
            {
                UpdateInstantiatedObjectPositions(); //reinsantiated object entries
            }

        }

        void Update()
        {
            //dynamic spacing changes so that setups can be fixed if too close together or apart - intially for testing
            if (prevSpacing != spacing)
            {
                prevSpacing = spacing;
                GenerateGrid();
                Invoke("PrintCollisionReport", 0.1f);
            }

            if (Input.GetKeyDown(KeyCode.P)) // Press P to print collision data
            {
                PrintCollisionReport();
            }
        }


        //Reinstantiate all object entries at the origin al locations
        private void UpdateInstantiatedObjectPositions()
        {
            ClearGrid(); //doesnt delete runtime objects ie obj gen objects

            foreach (var entry in objectEntries)
            {
                if (entry.instantiatedGameObject == null) //not instantiated gameObjects, instantiate ie presets prefabs
                {
                    GameObject child = Instantiate(entry.prefab);
                    entry.instantiatedGameObject = child; //update status

                    //Collision Data gathering
                    CollisionData reporter = child.GetComponent<CollisionData>();
                    if (reporter != null)
                    {
                        reporter.objectName = entry.prefab.name;
                    }
                }

                //only update coords if already instantiated
                Vector3 coord = entry.position;

                if (coord.x >= 0 && coord.x < gridsize && coord.y >= 0 && coord.y < gridsize && coord.z >= 0 && coord.z < gridsize)
                {
                    Rigidbody rb = entry.instantiatedGameObject.GetComponent<Rigidbody>();
                    bool wasKinematic = true; // Assume true

                    // If the object is currently grabbed, DO NOT force its position or change its kinematic state.
                    var grabInteractable = entry.instantiatedGameObject.GetComponent<UnityEngine.XR.Interaction.Toolkit.XRGrabInteractable>();
                    if (grabInteractable != null && grabInteractable.isSelected)
                    {
                        continue; // Skip this object if it's being actively grabbed
                    }

                    if (rb != null)
                    {
                        // Store original kinematic state
                        wasKinematic = rb.isKinematic;
                        // Temporarily set to kinematic to allow direct transform manipulation
                        rb.isKinematic = true;
                        rb.Sleep();
                    }

                    coord = IsPositionOccupied(coord, occupiedPositions);
                    occupiedPositions.Add(coord);

                    Vector3 finalLocalPosition = new Vector3(coord.x * spacing, coord.y * spacing, coord.z * spacing);

                    entry.instantiatedGameObject.transform.SetParent(gridParent.transform);
                    entry.instantiatedGameObject.transform.localPosition = finalLocalPosition;
                    entry.instantiatedGameObject.transform.localRotation = entry.initialRotation;

                    // Restore original kinematic state after positioning
                    if (rb != null)
                    {
                        rb.isKinematic = wasKinematic;
                        if (!rb.isKinematic)
                        {
                            rb.WakeUp();
                        }
                    }
                }
                else
                {
                    Debug.LogWarning($"Warning: {entry.instantiatedGameObject.name} has invalid coordinates ({coord.x},{coord.y},{coord.z}). Skipping.");
                }

            }

        }



        Vector3 IsPositionOccupied(Vector3 coord, List<Vector3> occupiedPositions, float tolerance = 0.01f)
        {
            foreach (var p in occupiedPositions)
            {
                if (Vector3.Distance(coord, p) < tolerance)
                {
                    //alter same place positions
                    //try displace up by tolerance amount
                    coord = DisplacePositionRandomly(coord, tolerance * 1.1f, tolerance * 2);

                    if (coord.x >= 0 && coord.x < this.gridsize && coord.y >= 0 && coord.y < this.gridsize && coord.z >= 0 && coord.z < this.gridsize)
                    {
                        return IsPositionOccupied(coord, occupiedPositions);
                    }
                    else
                    {
                        Debug.LogWarning($"Warning: Invalid coordinates ({coord.x},{coord.y},{coord.z}). Skipping.");
                    }
                }
            }
            return coord;
        }

        //if a grid collison does exist force a tolerance sepeartion to prevent direct generation ontop of each other
        private Vector3 DisplacePositionRandomly(Vector3 originalCoord, float minOffset, float maxOffset)
        {
            Vector3 randomOffset = UnityEngine.Random.insideUnitSphere * UnityEngine.Random.Range(minOffset, maxOffset);
            return originalCoord + randomOffset;
        }

        //wipes the current positions of objects so that objects can be reinstantiated
        void ClearGrid()
        {
            occupiedPositions.Clear();
        }


        //wipes runtime obj and clear current positions so that a new MOG setup can replace the old one
        void WipeGrid()
        {
            occupiedPositions.Clear();
            foreach (var obj in objectEntries)
            {
                if (obj != null)
                {
                    DestroyImmediate(obj.instantiatedGameObject);
                    obj.instantiatedGameObject = null; //nullify reference
                    obj.prefab = null;
                }
            }
            objectEntries.Clear();
        }


        // New method to retrieve collision data
        public Dictionary<string, Dictionary<string, List<string>>> GetAllCollisionData()
        {
            Dictionary<string, Dictionary<string, List<string>>> collisionReport = new Dictionary<string, Dictionary<string, List<string>>>();
            foreach (var entry in objectEntries)
            {
                CollisionData reporter = entry.instantiatedGameObject.GetComponent<CollisionData>();
                if (reporter != null)
                {
                    collisionReport[reporter.name] = new Dictionary<string, List<string>>(reporter.collidingWith); // Create a copy
                }
            }
            return collisionReport;
        }


        void PrintCollisionReport()
        {
            Dictionary<string, Dictionary<string, List<string>>> currentCollisions = GetAllCollisionData();
            Debug.Log("--- Current Collision Report ---");
            foreach (var reportingObjectEntry in currentCollisions)
            {
                // reportingObjectEntry.Key is the name of the object reporting the collisions
                // reportingObjectEntry.Value is the Dictionary<string, List<string>> of its collisions

                string reporterName = reportingObjectEntry.Key;
                Dictionary<string, List<string>> collidedObjectsDetails = reportingObjectEntry.Value;

                if (collidedObjectsDetails != null && collidedObjectsDetails.Count > 0)
                {
                    Debug.Log($"Object: {reporterName} is colliding with:");

                    // Iterate through the inner dictionary (collided objects and their details)
                    foreach (var collidedObjectDetailEntry in collidedObjectsDetails)
                    {
                        // collidedObjectDetailEntry.Key is the name of the object it collided with
                        // collidedObjectDetailEntry.Value is the List<string> of contact points

                        string collidedName = collidedObjectDetailEntry.Key;
                        List<string> contactPointsStrings = collidedObjectDetailEntry.Value;

                        if (contactPointsStrings != null && contactPointsStrings.Any())
                        {
                            // Use string.Join to combine all contact point strings into one readable line
                            string contactsInfo = string.Join(",", contactPointsStrings);
                            Debug.Log($"  - Object: {collidedName} Contact Points: - {contactsInfo}");
                        }
                        else
                        {
                            Debug.Log($"  - Object: {collidedName} (No specific contact points reported)");
                        }
                    }
                }
                else
                {
                    Debug.Log($"Object: {reporterName} is not colliding with anything.");
                }
            }
            Debug.Log("------------------------------");
        }



    }

}