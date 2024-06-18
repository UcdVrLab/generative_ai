using System.Collections.Generic;
using UnityEngine;
using System.IO;

public class JsonHelper {
    public static string ReadJsonFile(string filePath) {
        string jsonString = File.ReadAllText(filePath);
        if (jsonString != null) {
            return jsonString;
        } else {
            Debug.LogError("Failed to load JSON file");
            return null;
        }
    }
}
