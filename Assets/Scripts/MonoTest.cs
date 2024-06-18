using System.IO;
using System.Linq;
using MeshProcess;
using UnityEditor;
using UnityEngine;
using Mesh = Dummies.Mesh;

public class MonoTest : MonoBehaviour {
    public Mesh mesh = new();
    [SerializeField] public GameObject test;

    public void LoadMesh() {
        var data = File.ReadAllBytes(Path.Combine(Application.streamingAssetsPath, "mesh.bin"));
        mesh.SetBytes(data);
        var filter = gameObject.GetComponent<MeshFilter>();
        filter.sharedMesh = mesh.ToUnityMesh();
        var renderer = gameObject.GetComponent<MeshRenderer>();
        renderer.material = new(Shader.Find("Particles/Standard Surface")); 
    }
}

[CustomEditor(typeof(MonoTest))]
public class MonoTestEditor : Editor {
    public override void OnInspectorGUI()
    {
        base.OnInspectorGUI();

        var monoTest = (MonoTest)target;

        if (GUILayout.Button("Load Mesh"))
        {
            monoTest.LoadMesh();
        }

        if (GUILayout.Button("Generate Convex Mesh"))
        {
            GenerateConvexMesh(monoTest);
        }
    }

    private void GenerateConvexMesh(MonoTest monoTest)
    {
        // Print the time it took
        float startTime = Time.realtimeSinceStartup;

        // Perform VHACD computation here (similar to your Update method logic)
        var convexHulls = AsyncVHACD.GenerateConvexMeshes(monoTest.mesh);

        float endTime = Time.realtimeSinceStartup;
        float elapsedTime = endTime - startTime;
        Debug.Log($"Convex mesh generation took: {elapsedTime} seconds");
        var other = monoTest.test;
        other.GetComponents<MeshCollider>().ToList().ForEach(DestroyImmediate);
        convexHulls.ForEach(ch => {
            var collider = other.AddComponent<MeshCollider>();
            collider.sharedMesh = ch.ToUnityMesh();
            collider.convex = true;
        });
    }
}