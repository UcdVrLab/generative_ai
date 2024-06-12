using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Valve.VR;
using Valve.VR.InteractionSystem;

public class MergeableParent : MonoBehaviour {
    public SteamVR_Action_Boolean pinchAction = SteamVR_Actions.default_GrabPinch;
    private static int mergingLayer = 20;
    private int originalLayer;
    public List<MergeableChild> children = new();
    public int wasHolding = 0;
    private void Start() {
        originalLayer = gameObject.layer;
        if(children.Count == 0) AssignChildren();
        var rb = gameObject.GetComponent<Rigidbody>();
        children.ForEach(c => {
            rb.mass += c.mass;
        });
        tag = "Mergeable";
    }

    private void Update() {
        if(--wasHolding < 0) wasHolding = 0;
    }

    private void AssignChildren() {
        for(int i=0;i<gameObject.transform.childCount;i++) {
            var child = gameObject.transform.GetChild(i);
            children.Add(child.gameObject.GetComponent<MergeableChild>());
        }
    }

    private void AddAllColiders(List<Collider> colliders) {
        colliders.ForEach(col => {
                var colider = gameObject.AddComponent<Collider>();
                colider = col;
            });
    }

    private void HandHoverUpdate(Hand hand) {
        if(hand?.isActive != null) {
            if(pinchAction.GetStateDown(hand.handType)) {
                Debug.Log("Switching to pass through layer");
                SetLayersOnAll(mergingLayer);
            } else if (pinchAction.GetStateUp(hand.handType)) {
                Debug.Log("Reverting to normal layer");
                SetLayersOnAll(originalLayer);
            } 
            
        }
    }
    private void OnDetachedFromHand(Hand _) {
        if(gameObject.layer != originalLayer) {
            Debug.Log("Reverting to normal layer");
            SetLayersOnAll(originalLayer);
        }
        wasHolding = 20;
    }

    public void OnSplit(List<Children> childrenToRemove) {
        //Create a new parent for the children
        //Calculate new rb masses
        //Assign colliders
    }

    public void OnMerge(MergeableParent other) {
        GetComponent<Rigidbody>().mass += other.GetComponent<Rigidbody>().mass;
        other.children.ForEach(c => c.OnMerge(this));
        children.AddRange(other.children);
        other.gameObject.SetActive(false);
        Destroy(other.gameObject);
        wasHolding = 0;
    }

    private void SetLayersOnAll(int layer) {
        gameObject.layer = layer;
        children.ForEach(c => c.gameObject.layer = layer);
    }

    private void OnCollisionEnter(Collision collision) {
        var other = collision.collider.gameObject;
        if (other.CompareTag("Mergeable")) {
            var otherparent = other.GetComponent<MergeableChild>().parent;
            Debug.Log($"other: {otherparent.wasHolding}, me: {wasHolding}");
            if(otherparent.wasHolding > 0) {
                Debug.Log("Merging");
                OnMerge(otherparent);
            }
        }
    }
}