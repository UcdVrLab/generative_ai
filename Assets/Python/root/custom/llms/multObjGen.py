from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
from custom.llms.custompipeline import TruePipeline
from datastructs.datalist import Entry
from networking.serializer import Serializer
from custom.llms.multObjGenContext import *
from custom.llms.multObjGenFunctions import *
from custom.serializers.default import MOGCoordinateMap


'''
Developed by: Michal Laneki and Jeric Antony
Description: Series of AI assistant agents that create a dictionary of objects and their positions in grid as part of a setup/scene
Original MOG pipeline made by Michal Laneki and expanded on by Jeric Antony 20/08/25
'''
class MultObjGen(TruePipeline):
    def __init__(self, model, tokenizer):
        super().__init__(model, tokenizer)
        self.object_list_assistant = ObjectListAssistant(self.pipe, objlist_context) #creates a list of objects
        self.relational_mapping_assistant = RelationalMappingAssistant(self.pipe, relational_context) #gives spatial relations between each object
        self.grid_placement_assistant = GridPlacementAssistant(self.pipe, grid_context) #uses an anchor and spatial relations to develop a grid with ai determining the separation
        self.grid_resolver_assistant = GridCollisionAssistant(self.pipe, grid_resolver_context) #resolves objects in the same grid space with either horizontal or vertical separation based on their spatial relations
        self.max_tries = 10

    @classmethod     
    def name(cls):
        return "MULTOBJGEN"
    
    @classmethod 
    def max_tokens(cls):
        return 50
    
    @classmethod 
    def system_prompt(cls):
        return '''
        '''
    
    def prompt(self, prompt):
        tries = 0
        # 1 - prompt -> objectlist (str)

        while tries < self.max_tries: #do while to get object list, to ensure no code breaks while system is running - Made by Jeric Antony
            object_list_raw = self.object_list_assistant.process_request(prompt)
            # 2 - objectlist (str) -> setName (str), objectList (list)
            set_name, object_list = parse_complete_prompt(object_list_raw)
            tries+=1

            if isinstance(object_list, list):
                break

        if tries == self.max_tries:
            return ("CONFUSED",)

        # 3 - objectlist (list) -> relationsList (str)
        relations = self.relational_mapping_assistant.process_request(object_list)
        print(f"\n  {relations}")


        # # 4 - relationsList (str) -> objectCoordinateList (str)
        # coordinates_raw = self.grid_placement_assistant.process_request(relations)
        # print(f"\n  {coordinates_raw}")
        # # 5 objectCoordinateList (str) -> coordinateDict (dict)

        #coordinates : MOGCoordinateMap = MOGCoordinateMap(parse_coordinates(coordinates_raw))

        # 4 - relationsList (str) -> coordinateDict (dict)
        coordinates : MOGCoordinateMap = MOGCoordinateMap(self.grid_placement_assistant.grid_relation_alignment(relations)) #Change to pipeline by Jeric Antony for better consistency with spatial relations

        
        print(coordinates)


        #--- Process created by Jeric Antony 
        #6 same space objects
        duplicate_coords = find_duplicate_coords(coordinates)
        #only pass if there are duplicates
        if duplicate_coords:
            batch_resolved_coords_raw = self.grid_resolver_assistant.process_request(duplicate_coords, relations)
            for single_resolved_coord_raw in batch_resolved_coords_raw:
                resolved_coords = parse_coordinates_3D(single_resolved_coord_raw)
                coordinates.update(resolved_coords)
        coords_to_3D(coordinates)
        #---

        print(coordinates)

        return (set_name, coordinates)


    @classmethod 
    def service(cls) -> str:
        return "MOGHandler"

    @classmethod 
    def spoken(cls, result) -> str:
        set_name, object_coord_dict = result
        object_names = ", ".join(object_coord_dict.keys())
        return f"Creating a {set_name} scene with objects {object_names}."

    @classmethod 
    def to_entries(cls, result) -> list[Entry]:
        set_name, object_coord_dict = result
        return [Entry("set_name", set_name), Entry("objects.coords", object_coord_dict)]
    

