from queue import Queue
from processing.streams import MultiLabelList
from datastructs.datalist import DataList, Entry
from processing.services import MultiTransformation, Transformation

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from custom.llms.Controller import Controller
from custom.llms.ObjGen import ObjGen
from custom.llms.Converse import Converse
from custom.llms.SkyGen import SkyGen
from custom.llms.Answerer import Answerer
from custom.llms.custompipeline import Confused,Terminator,Pipeline

print("Starting to load LLama2 model")
model_name_or_path = "TheBloke/Llama-2-7b-Chat-GPTQ"
model = AutoModelForCausalLM.from_pretrained(
    model_name_or_path, device_map="cuda", trust_remote_code=False, revision="main")
tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)
print("Finished loading LLama2 model")

class LLMController(MultiTransformation):
    def setup(self):
        self.max_tries = 20
        # self.send_special([(self.create_special_dl(DataList(), Entry("log", f"LLama2 Initializing")), ["Debugger"])])        
        self.setup_pipelines()
        self.send_special([(self.create_special_dl(DataList(), Entry("log", f"LLama2 Loaded")), ["Debugger"])])

    def setup_pipelines(self):
        self.controller = Controller(model, tokenizer)
        self.experts: list[Pipeline] = [
            ObjGen(model, tokenizer),
            Converse(model, tokenizer),
            SkyGen(model, tokenizer),
            Answerer(model, tokenizer),
            Terminator(),
            Confused(),
        ]

    def get_expert(self, command: str):
        return next((e for e in self.experts if e.name() == command), None)

    def super_prompt(self, prompt: str):
        command = details = ""
        tries = 0
        while isinstance(command, str) and tries < self.max_tries: 
            command = self.controller.prompt(prompt)
            tries += 1
            if(isinstance(command, str)): 
                print(f"No command given: {command}")
        if tries == self.max_tries:
            command = ("CONFUSED",)
        expert = self.get_expert(command[0])
        if expert:
            tries = 0
            while isinstance(details, str) and tries < self.max_tries: 
                details = expert.prompt(prompt)
                tries += 1
                if(isinstance(details, str)): 
                    print(f"Incorrect details: {details}")
            if tries == self.max_tries:
                command = ("CONFUSED",)
                details = self.get_expert(command[0]).prompt(prompt)
        else:
            print("Command not defined")
        return (prompt, command, details)

    def process(self, dl: DataList) -> MultiLabelList:
        prompt = f"User: {dl.pop_content_by_message('prompt').data}"
        mll = []
        gtts_dl = dl.shallow_copy()
        debug_dl = dl.shallow_copy()

        _, command, details = self.super_prompt(prompt)
        expert = self.get_expert(command[0])
        print(f"Command: {command}, details: {details}, expert: {expert}")
        if expert:
            if expert.service():
                service_dl = dl.shallow_copy()
                service_dl.add_contents(expert.to_entries(details))
                mll.append((service_dl, [expert.service()]))
            elif expert.name == "TERMINATE":
                # need to terminate, but not instantly
                pass
            gtts_dl.add_content(Entry("message", expert.spoken(details)))
            debug_dl.add_content(Entry("log", "System: " + expert.spoken(details)))
        else:
            gtts_dl.add_content(Entry("message", f"Failure to understand intent: Unknown command '{command}'"))
        mll.append((gtts_dl, ["GTTS"]))
        mll.append((debug_dl, ["Debugger"]))
        return mll
    
from datastructs.npc import *
    
class NPCLLMs(MultiTransformation):
    npcs: dict[int,NPC] = {}
    global_id = 1  # 0 is player

    def setup(self):
        self.npcs[0] = NPC(0, "Player", "The player", None, None) 

    def create_npc(self, name, desc):
        old = self.npcs.pop(next((k for k,_ in self.npcs.items() if k != 0), None), None)   #remove old npc
        if old: print(f"Removed npc = {old}")
        npc = NPC(self.global_id, name, desc, model, tokenizer)
        self.npcs[self.global_id] = npc
        self.global_id += 1
        return npc
    
    def get_creation_details(self, dl: DataList) -> tuple[str,str,str]: 
        return dl.pop_content_to_tuple_by_messages("npc.create-name", "npc.create-desc", "npc.create-appearance")

    def get_talking_details(self, dl: DataList) -> tuple[int, list[int], str]:
        sid, lids, tm = dl.pop_content_to_tuple_by_messages("npc.talk-speaker_id", "npc.talk-listener_ids", "npc.talk-message")
        return (sid, [int(s) for s in lids.split(',')], tm)
    
    def valid_talking_details(self, sid, lid, tm) -> bool:
        return sid >= 0 and lid and tm
    
    def create_npc_creation_message(self, dl: DataList, name: str, appearance: str, id: int):
        return dl.shallow_copy(new_contents=[Entry("prompt", f"{name}: {appearance}"), Entry("npc.create-name", name), Entry("npc.create-id", id)])
    
    def create_unity_talk_message(self, dl: DataList, id: int, plain_response: str):
        return dl.shallow_copy(new_contents=[Entry("npc.talk-speaker_id", id), Entry("npc.talk-message", plain_response)])
    
    def process(self, dl: DataList) -> MultiLabelList:
        creation = self.get_creation_details(dl)
        if all(creation):
            npc = self.create_npc(creation[0], creation[1])
            return [(self.create_npc_creation_message(dl, creation[0], creation[2], npc.id), ["StableDiffusion"])]
        else:
            sid,lids,msg = self.get_talking_details(dl)
            if self.valid_talking_details(sid,lids,msg):
                speaker_npc = self.npcs[sid]
                message = f"{speaker_npc.name}: {msg}"
                for npc in [self.npcs[id] for id in lids if id != 0]:
                    npc.hear(message)
                    response = npc.respond()
                    plain_response = response.split(': ', 1)[1]
                    if response:
                        self.send_special([(self.create_special_dl(DataList(), Entry("message", plain_response)), ["GTTS"])])
                        self.send_special([(self.create_special_dl(DataList(), Entry("log", response)), ["Debugger"])])
                        return [(self.create_unity_talk_message(dl, npc.id,plain_response), ["NPCHandler"])]
                    else: print("No response...")
            else:
                print("No proper data was found in " + dl.__str__())
        return []
