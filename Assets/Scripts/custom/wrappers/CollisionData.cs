using UnityEngine;
using System.Collections.Generic;


/*
 * File: CollisionData.cs
 * Author: Jeric Antony
 * Created: 20/08/25
 * Description: Collates information in a dict for every object and what it is colliding with, where and by how much
*/

public class CollisionData : MonoBehaviour
{
    public string objectName; // To identify which object this is

    // This list will store information about objects it's colliding with
    public Dictionary<string, List<string>> collidingWith = new Dictionary<string, List<string>>();

    void Start()
    {
        // Ensure this object has a collider for collision detection
        if (GetComponent<Collider>() == null)
        {
            Debug.LogWarning($"Object '{gameObject.name}' is missing a Collider component. Collision events won't fire.");
        }

        // If using OnTriggerEnter, only one needs a Rigidbody and the collider needs 'Is Trigger' checked
        if (GetComponent<Rigidbody>() == null && !GetComponent<Collider>().isTrigger)
        {
            Debug.LogWarning($"Object '{gameObject.name}' is missing a Rigidbody, or its Collider is not a Trigger. OnCollisionEnter may not fire reliably with static colliders.");
        }
    }

    // Called when this collider has begun touching another collider (physical collision)
    void OnCollisionEnter(Collision collision)
    {
        // Only consider if the other object also has a collider
        if (collision.collider != null)
        {
            string otherObjectName = collision.collider.gameObject.name;
            // Avoid self-collision issues if objects spawn very close
            if (otherObjectName != gameObject.name && !collidingWith.ContainsKey(otherObjectName))
            {
                foreach (ContactPoint contact in collision.contacts)
                {
                    AddValue(collidingWith, otherObjectName, $"{contact.point} Separation: {contact.separation}");

                }
            }
        }
    }

    // Called when this collider has stopped touching another collider
    void OnCollisionExit(Collision collision)
    {
        if (collision.collider != null)
        {
            string otherObjectName = collision.collider.gameObject.name;
            if (collidingWith.ContainsKey(otherObjectName))
            {
                collidingWith.Remove(otherObjectName);
                //Debug.Log($"{objectName} stopped colliding with {otherObjectName} at {Time.time}");
            }
        }
    }

    // Helper method to add values gracefully
    public static void AddValue<TKey, TValue>(Dictionary<TKey, List<TValue>> dictionary, TKey key, TValue value)
    {
        if (dictionary.TryGetValue(key, out List<TValue> list))
        {
            // Key exists, add to existing list
            list.Add(value);
        }
        else
        {
            // Key doesn't exist, create new list and add
            dictionary.Add(key, new List<TValue> { value });
        }
    }

}