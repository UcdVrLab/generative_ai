using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;

public static class Util {
    public static List<Type> GetBaseclasses(this Type type) {
        List<Type> baseClasses = new();
        var cur = type;
        while(cur != typeof(object)) {
            baseClasses.Add(cur);
            cur = cur.BaseType;
        }
        baseClasses.Add(typeof(object));
        return baseClasses;
    }

    public static List<Type> GetTypesInNamespace(string nameSpace) {
        return Assembly.GetExecutingAssembly().GetTypes()
                .Where(t => string.Equals(t.Namespace, nameSpace, StringComparison.Ordinal))
                .ToList();
    }

    public static byte[] VectorToBytes(this Vector3 v) {
        return ConcatBytes(BitConverter.GetBytes(v.x), BitConverter.GetBytes(v.y), BitConverter.GetBytes(v.z));
    }

    public static Vector3 BytesToVector(this byte[] bytes) {
        return new(BitConverter.ToSingle(bytes[0..4]), BitConverter.ToSingle(bytes[4..8]), BitConverter.ToSingle(bytes[8..12]));
    }

    public static byte[] ColorToBytes(this Color32 color) {
        return new byte[] { color.r, color.g, color.b};
    }

    public static Color32 BytesToColor(this byte[] bytes) {
        return new(bytes[0], bytes[1], bytes[2], 0xFF);
    }

    public static T[] BytesToArray<T>(this byte[] bytes, Func<byte[], T> converter, int dsize) {
        var arr = new T[bytes.Length / dsize];
        for(int i=0;i < bytes.Length; i+=dsize) {
            arr[i/dsize] = converter(bytes[i..(i+dsize)]);
        }
        return arr;
    }

    public static byte[] ArrayToBytes<T>(this T[] arr, Func<T, byte[]> converter) {
        return arr.SelectMany(a => converter(a)).ToArray();
    }

    public static byte[] ConcatBytes(params byte[][] bytes) {
        return bytes.SelectMany(b => b).ToArray();
    }

    public static void WriteCollectionToFile<T>(IEnumerable<T> values, string filePath) {
        try {
            using StreamWriter sw = new(filePath);
            foreach (var item in values) {
                sw.WriteLine(item);
            }
        } catch (Exception ex) {
            Debug.LogError(ex);
        }
    }
}

