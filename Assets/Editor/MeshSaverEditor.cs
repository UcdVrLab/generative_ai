using UnityEngine;
using UnityEditor; // Required for editor-specific functionalities
using System.IO;   // Required for file path operations


// The main Editor script - Jeric Antony - 20/08/25
// Gemini Assisted Editor Script for saving ShapE runtime prefabs correctly as pregenerated prefabs through saving the mesh/material/colliders correctly
// Allows runtime prefabs to be saved into prefabs folder and then be used as again as asset prefabs 
public static class MeshSaverEditor // Changed back to static class (no MonoBehaviour)
{
    private const string SETTINGS_PATH = "Assets/Editor/MeshSaverSettings.asset"; // Path for the settings asset

    [MenuItem("Tools/Save Generated Mesh as Asset & Material & Colliders")]
    public static void SaveSelectedMeshAsAssetAndMaterialAndColliders()
    {
        // 1. Get the currently selected GameObject in the Hierarchy
        GameObject selectedGameObject = Selection.activeGameObject;

        // Basic validation: Check if a GameObject is selected
        if (selectedGameObject == null)
        {
            Debug.LogWarning("No GameObject selected. Please select the GameObject containing the generated mesh in the Hierarchy.");
            return;
        }

        // 2. Get or Add the MeshFilter component
        MeshFilter meshFilter = selectedGameObject.GetComponent<MeshFilter>();
        if (meshFilter == null)
        {
            Debug.LogWarning("Selected GameObject does not have a MeshFilter. Adding one.");
            meshFilter = selectedGameObject.AddComponent<MeshFilter>();
        }

        // More validation: Check if a mesh is assigned to the MeshFilter
        if (meshFilter.sharedMesh == null)
        {
            Debug.LogWarning("The MeshFilter on the selected GameObject does not have a mesh assigned. Please ensure your mesh generation process assigns a mesh to the MeshFilter.");
            return;
        }

        // The mesh we want to save (using sharedMesh to get the actual mesh data)
        Mesh meshToSave = meshFilter.sharedMesh;

        // 3. Get or Add the MeshRenderer component
        MeshRenderer meshRenderer = selectedGameObject.GetComponent<MeshRenderer>();
        if (meshRenderer == null)
        {
            Debug.LogWarning("Selected GameObject does not have a MeshRenderer. Adding one.");
            meshRenderer = selectedGameObject.AddComponent<MeshRenderer>();
        }

        // --- Handle Mesh Saving ---

        // Create a unique path for the mesh asset
        string meshName = selectedGameObject.name + "_GeneratedMesh";
        string meshPath = EditorUtility.SaveFilePanelInProject("Save Generated Mesh Asset", meshName, "asset", "Enter a file name for the generated mesh asset.");

        if (string.IsNullOrEmpty(meshPath))
        {
            Debug.Log("Mesh asset saving cancelled by user.");
            return;
        }

        // Ensure the directory for the mesh asset exists
        string meshDirectory = Path.GetDirectoryName(meshPath);
        if (!Directory.Exists(meshDirectory))
        {
            Directory.CreateDirectory(meshDirectory);
        }

        // Create a *copy* of the mesh data before saving to ensure independence
        Mesh newMeshAsset = Object.Instantiate(meshToSave);
        newMeshAsset.name = meshName;

        // Save the new mesh asset
        AssetDatabase.CreateAsset(newMeshAsset, meshPath);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh(); // Refresh to make the mesh asset visible

        Debug.Log($"Successfully saved mesh to: {meshPath}");

        // Update the MeshFilter on the original GameObject to reference the newly saved permanent asset.
        meshFilter.sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);


        // --- Handle Material Saving and Assignment ---

        Material materialToAssign = meshRenderer.sharedMaterial;

        // If no material is currently assigned to the MeshRenderer, create a default one
        // and assign it using the explicitly set Shader Graph shader.
        if (materialToAssign == null || AssetDatabase.GetAssetPath(materialToAssign) == "") // Check if it's a valid asset material
        {
            Debug.LogWarning("No existing material found or assigned. Creating a new default material.");

            // Load or create the MeshSaverSettings ScriptableObject
            MeshSaverSettings settings = AssetDatabase.LoadAssetAtPath<MeshSaverSettings>(SETTINGS_PATH);
            if (settings == null)
            {
                settings = ScriptableObject.CreateInstance<MeshSaverSettings>();
                AssetDatabase.CreateAsset(settings, SETTINGS_PATH);
                AssetDatabase.SaveAssets();
                Debug.LogWarning($"MeshSaverSettings asset created at {SETTINGS_PATH}. Please assign your Shader Graph assets in its Inspector.");
            }

            Shader selectedShader = null;

            if (settings.defaultShaderGraph != null)
            {
                selectedShader = settings.defaultShaderGraph;
                Debug.Log($"Using default Shader Graph from settings: {selectedShader.name}");
            }
            else
            {
                // Fallback if no Shader Graph is assigned in settings
                selectedShader = Shader.Find("Universal Render Pipeline/Lit");
                if (selectedShader == null)
                {
                    selectedShader = Shader.Find("Unlit/Color"); // Absolute fallback
                    Debug.LogError("Could not find 'Universal Render Pipeline/Lit' shader. Defaulting to 'Unlit/Color'. Please ensure URP is installed and shaders are available, or assign a custom shader in the 'MeshSaverSettings' asset's Inspector.");
                }
                else
                {
                    Debug.Log("Using default 'Universal Render Pipeline/Lit' shader as no custom shader was assigned in settings.");
                }
            }


            Material newDefaultMaterial = new Material(selectedShader);
            newDefaultMaterial.color = Color.white; // Set a default color

            // Create a unique path for the material asset,
            // placing it in the same directory as the mesh for convenience
            string materialName = selectedGameObject.name + "_GeneratedMaterial";
            string materialPath = Path.Combine(meshDirectory, materialName + ".mat");

            // Save the new material asset
            AssetDatabase.CreateAsset(newDefaultMaterial, materialPath);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(); // Refresh to make the material asset visible

            materialToAssign = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            Debug.Log($"Successfully created and saved default material to: {materialPath}");
        }

        // Assign the (either existing or newly created) material to the MeshRenderer
        meshRenderer.sharedMaterial = materialToAssign;

        // --- Handle MeshCollider Assignment ---
        // Get all MeshCollider components on the selected GameObject and its children
        MeshCollider[] meshColliders = selectedGameObject.GetComponentsInChildren<MeshCollider>();

        if (meshColliders.Length > 0)
        {
            Debug.Log($"Found {meshColliders.Length} MeshCollider(s) on the selected GameObject or its children. Assigning the saved mesh to them.");
            foreach (MeshCollider collider in meshColliders)
            {
                // Assign the newly saved mesh asset to each MeshCollider
                collider.sharedMesh = newMeshAsset;
                Debug.Log($"Assigned mesh '{newMeshAsset.name}' to MeshCollider on GameObject: {collider.gameObject.name}");
            }
        }
        else
        {
            Debug.Log("No MeshCollider components found on the selected GameObject or its children. If needed, please add them manually.");
        }

        Debug.Log("GameObject's MeshRenderer and any MeshColliders updated with valid assets. You can now drag this GameObject into your Project window to create a prefab that will retain its mesh, material, and collider configurations.");
    }
}
