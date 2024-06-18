using System;
using System.Linq;
using MeshProcess;
using UnityEngine;
using UnityEngine.XR;
using Valve.VR.InteractionSystem;
using UnityMesh = UnityEngine.Mesh;

namespace Dummies {
    public abstract class Dummy {
    protected byte[] bytes;

    public Dummy() {}
    public virtual void SetBytes(byte[] bytes) {
        this.bytes = bytes;
    }
    public virtual byte[] ToBytes() { return bytes; }
}

public  class Image : Dummy {
    public Image() : base() {}
    public Image(Texture2D texture) {
        byte[] imageBytes = texture.GetRawTextureData();
        byte[] width = Serializer.ToBytes(texture.width);
        byte[] height = Serializer.ToBytes(texture.height);
        bytes = width.Concat(height).Concat(imageBytes).ToArray();
    }

    public Texture2D ToTexture() {
        int width = (int)Serializer.FromBytes<long>(bytes.Take(8).ToArray());
        int height = (int)Serializer.FromBytes<long>(bytes.Skip(8).Take(8).ToArray());
        Texture2D image = new(width, height, TextureFormat.RGB24, false);
        image.LoadRawTextureData(bytes.Skip(16).ToArray());
        image.Apply();
        return image;
    } 
}

public class Audio : Dummy {
    public Audio() : base() {}
    public Audio(AudioClip clip) {
        bytes = WavUtility.FromAudioClip(clip);
    }

    public AudioClip ToAudioClip() {
        return WavUtility.ToAudioClip(bytes);
    }
}

public class Mesh : Dummy {
    public Mesh() : base() {}
    public Vector3[] Vertices {get; set;}
    public int[] Faces {get; set;}
    public Color32[] VertColors {get; set;}

    public Mesh(UnityMesh unityMesh) {
        Vertices = unityMesh.vertices;
        Faces = unityMesh.triangles;
        VertColors = unityMesh.colors32;
    }

    public UnityMesh ToUnityMesh() {
        UnityMesh mesh = new() { vertices = Vertices, triangles = Faces, colors32 = VertColors };
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
        return mesh;
    }

    public override void SetBytes(byte[] bytes) {
        var nv = BitConverter.ToUInt16(bytes, 0);
        var v_size = nv*4*3;
        var vc_size = nv*1*3;
        Vertices = bytes[2..(2+v_size)].BytesToArray(b => b.BytesToVector(), 12);
        VertColors = bytes[(2+v_size)..(2+v_size+vc_size)].BytesToArray(b => b.BytesToColor(), 3);
        var nf = BitConverter.ToUInt32(bytes, 2+v_size+vc_size);
        var f_size = nf*2*3;
        Faces = bytes[(6+v_size+vc_size)..].BytesToArray(b => (int)BitConverter.ToUInt16(b), 2);
        if(Faces.Length != f_size/2) {
            throw new Exception($"Mesh data was not valid, faces: {Faces.Length} != {f_size}");
        }
    }

    public override byte[] ToBytes() {
        var nv = BitConverter.GetBytes((ushort)Vertices.Length); 
        var v = Vertices.ArrayToBytes(v => v.VectorToBytes());
        var vc = VertColors.ArrayToBytes(c => c.ColorToBytes());
        var nf = BitConverter.GetBytes((uint)Faces.Length);
        var f = Faces.ArrayToBytes(f => BitConverter.GetBytes((ushort)f));
        return Util.ConcatBytes(nv, v, vc, nf, f);
    }
}
}