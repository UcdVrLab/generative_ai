using UnityEngine;
using UnityEditor;
using UnityEngine.XR;
using Valve.VR;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System;

public class NetworkManager : UpdateWrapper<DataList,SingleLabelList> {
    public string physicalLayout;
    public string virtualLayout;
    const string VIRTUAL_FOLDER = "Assets/Config/virtual"; 
    const string PHYSICAL_FOLDER = "Assets/Config/physical"; 

    void Start() {
        var physNet = JsonUtility.FromJson<PhysicalNetwork>(JsonHelper.ReadJsonFile($"{PHYSICAL_FOLDER}/{physicalLayout}.json"));
        var virtNet = JsonUtility.FromJson<VirtualNetwork>(JsonHelper.ReadJsonFile($"{VIRTUAL_FOLDER}/{virtualLayout}.json"));
        virtNet.Setup();
        var (self, peers) = Peers.GenerateP2PConnections("unity", physNet);
        ConfigEstablishment.ShareServicesWithPeers(self, peers);
        Debug.Log("Local Services that are available");
        Debug.Log(string.Join(",", self.services));
        Debug.Log("Remote Services that are available");
        peers.ForEach(p => Debug.Log(string.Join(",", p.services)));
        ConfigEstablishment.DetermineUsedServices(self, peers, virtNet);
        Debug.Log("Local Services that will be used");
        Debug.Log(string.Join(",", self.usedServices));
        AttachProcessor(new Handler(self, peers, virtNet));
        Debug.Log($"Setup finished, VR = {XRSettings.enabled}");
        processor.Start();
    } 

    public override SingleLabelList OnUpdate(DataList t) {
        return processor.Process(t);
    }

    public void OnApplicationQuit() {
        processor.InternalTerminate();
    }

    public (string[] vfiles, string[] pfiles) RefreshFileLists() {
        return (new DirectoryInfo(VIRTUAL_FOLDER).GetFiles().Select(f => f.Name).ToArray(),
                new DirectoryInfo(PHYSICAL_FOLDER).GetFiles().Select(f => f.Name).ToArray());
    }
}