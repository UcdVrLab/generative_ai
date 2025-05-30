from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
from multObjGenContext import *
from multObjGenFunctions import *


model_name_or_path = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GPTQ"
model = AutoModelForCausalLM.from_pretrained(model_name_or_path, device_map="cuda", trust_remote_code=False, revision="main")
tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)


pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=50,
    do_sample=True,
    temperature=0.7,
    top_p=0.95,
    top_k=40,
    repetition_penalty=1.1
)


object_list_assistant = ObjectListAssistant(pipe, objlist_context)
relational_mapping_assistant = RelationalMappingAssistant(pipe, relational_context)
grid_placement_assistant = GridPlacementAssistant(pipe, grid_context)


def multObjGen(prompt):
    # 1 - prompt -> objectlist (str)
    object_list_raw = object_list_assistant.process_request(prompt)
    # 2 - objectlist (str) -> setName (str), objectList (list)
    set_name, object_list = parse_complete_prompt(object_list_raw)
    # 3 - objectlist (list) -> relationsList (str)
    relations = relational_mapping_assistant.process_request(object_list)
    # 4 - relationsList (str) -> objectCoordinateList (str)
    coordinates_raw = grid_placement_assistant.process_request(relations)
    # 5 objectCoordinateList (str) -> coordinateDict (dict)
    coordinates = parse_coordinates(coordinates_raw)
    return coordinates
