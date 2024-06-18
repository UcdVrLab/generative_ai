using UnityEngine;

public class MergeableChild : MonoBehaviour {
    public float mass;
    public MergeableParent parent;

    public void Start() {
        mass = 1;
        parent = transform.parent.gameObject.GetComponent<MergeableParent>();
        tag = "Mergeable";
    }
    
    public void OnSplit(MergeableParent newParent) {
        //going from old to new
        //calculate new local transforms
    }

    public void OnMerge(MergeableParent newParent) {
        transform.GetLocalPositionAndRotation(out var locPos, out var locRot);
        var worldPos = parent.transform.TransformPoint(locPos);
        var worldRot = parent.transform.rotation * locRot;

        locPos = newParent.transform.InverseTransformPoint(worldPos);
        locRot = Quaternion.Inverse(newParent.transform.rotation) * worldRot;

        transform.SetLocalPositionAndRotation(locPos, locRot);
        transform.parent = newParent.transform;
        parent = newParent;
    }
}