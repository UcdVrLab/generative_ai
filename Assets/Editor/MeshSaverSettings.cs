using UnityEngine;
using UnityEditor; // Required for editor-specific functionalities
using System.IO;   // Required for file path operations

// ScriptableObject to hold editor settings - Jeric Antony - 20/08/25
// Gemini Assisted Editor Script for saving ShapE runtime prefabs correctly as pregenerated prefabs through saving the mesh/material/colliders correctly
// Allows runtime prefabs to be saved into prefabs folder and then be used as again as asset prefabs 
[CreateAssetMenu(fileName = "MeshSaverSettings", menuName = "ScriptableObjects/Mesh Saver Settings")] // Added this attribute
public class MeshSaverSettings : ScriptableObject
{
    [Header("Shader Graph Assignments (Drag your Shader Graph assets here)")]
    [Tooltip("The default Shader Graph asset to use for generated materials (e.g., 'normal' shader).")]
    public Shader defaultShaderGraph;

    [Tooltip("An optional 'metallic' Shader Graph asset.")]
    public Shader metallicShaderGraph;

    [Tooltip("An optional 'glowing' Shader Graph asset.")]
    public Shader glowingShaderGraph;

}