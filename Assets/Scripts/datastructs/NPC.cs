using System;
using Dummies;
using UnityEngine;

public class NPC : MonoBehaviour {
    public int Id;
    public Texture2D Image;
    public string Name;

    public void SetDetails((Image image, string name, int id) cd) {
        Name = cd.name;
        Image = cd.image.ToTexture();
        Id = cd.id;
        GetComponent<MeshRenderer>().material.mainTexture = Image;
        name = Name;
    }
}