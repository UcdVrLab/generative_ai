using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Dummies;
using MeshProcess;
using UnityEngine;
using UnityEngine.XR;
using Valve.VR.InteractionSystem;
using Mesh = Dummies.Mesh;

namespace Wrappers.Core {
    public class NPCHandler : UpdateWrapper<DataList,MultiLabelList> {
        public GameObject npcprefab, player;
        public Dictionary<int,NPC> npcs = new();
        public float hearingDistance = 10f;

        void Start() {
            var playerNPC = player.AddComponent<NPC>();
            playerNPC.Id = 0;
            playerNPC.name = "Player";
            npcs.Add(playerNPC.Id, playerNPC);
        }

        public override MultiLabelList OnUpdate(DataList dl) {
            var creationDetails = GetCreationDetails(dl);

            if(HasCreationDetails(creationDetails)) {
                var old = npcs.Values.Where(n => n.Id != 0).FirstOrDefault();
                CreateFromDetails(creationDetails);
                if(old != default(NPC)) { //gets too confusing with multiple npcs, they dont wait for each other to speak
                    npcs.Remove(old.Id);
                    Destroy(old.gameObject);
                }
                
                return new();
            } 
            return FillInSpeakerDetails(dl, DetermineSpeaker(dl));
        }

        private (Image image, string name, int id) GetCreationDetails(DataList dl) {
            return (dl.ContentPopper<Image>("diffused image")?.data,
                dl.ContentPopper<string>("npc.create-name")?.data,
                (int)(dl.ContentPopper<long>("npc.create-id")?.data ?? -1)
            );
        }
        private bool HasCreationDetails((Image image, string name, int id) cd) {
            return cd.image != null && cd.name != null && cd.id != -1;
        }

        private void CreateFromDetails((Image image, string name, int id) cd) {
            var npc = Instantiate(npcprefab, gameObject.transform).GetComponent<NPC>();
            npcs.Add(cd.id, npc);
            npc.SetDetails(cd);
        }
        private NPC DetermineSpeaker(DataList dl) {
            int speakerId = (int)(dl.ContentGetter<long>("npc.talk-speaker_id")?.data ?? 0);
            if(speakerId == 0) {
                dl.AddContent<string>(new("npc.talk-message", dl.ContentPopper<string>("prompt")?.data));
                dl.AddContent<long>(new("npc.talk-speaker_id", speakerId));
            }
            return npcs[speakerId];
        }

        public MultiLabelList FillInSpeakerDetails(DataList dl, NPC speaker) {
            var ids = npcs.Where(p => p.Key != speaker.Id).Select(p => p.Value)
                .Where(o => WithinEarshot(o, speaker)).Select(o => o.Id).ToList();
            if (ids.Count == 0) {
                Debug.Log("No one heard that...");
                return new();
            }
            return new() {(CreateTalkingDL(dl,ids), new(){"llm.NPCLLMs"})};
        }

        private bool WithinEarshot(NPC a, NPC b) {
            return (a.gameObject.transform.position - b.gameObject.transform.position).magnitude <= hearingDistance;
        }

        private DataList CreateTalkingDL(DataList dl, List<int> listenerIds) {
            var copy = dl.ShallowCopy();
            copy.AddContent<string>(new("npc.talk-listener_ids", string.Join(",", listenerIds)));
            return copy;
        }
    }
}