from custom.llms.custompipeline import TruePipeline
from datastructs.datalist import Entry

import re

class ObjGen(TruePipeline):
    def name(cls): return "OBJGEN"
    def max_tokens(cls):
        return 20
    def system_prompt(cls):
        return '''
            Assistant is a expert object creator and is able to determine what the object the user wants is and what material it is made of.
            Assistant will return the object that is to be generated, and the material.
            Format is Create: [object to create], Material: [material]
            All of Assistant's communication is performed using this format.

            Materials available to Assistant are:
            - "normal": The default material, if you do not know a better one.
            - "metallic": A shiny material used for objects made of metal.
            - "glowing": A material that emits light of a specific color.

            Here are some examples of conversations between user and Assistant:

            User: I am holding a sword
            Create: sword, Material: metallic

            User: A glowing diamond is in my hand
            Create: diamond, Material: glowing-white

            User: A large chair is on the ground
            Create: chair, Material: normal

            User: A pink vase is in front of me
            Create: vase, Material: metallic

            User: A burning torch appears in my hand
            Create: torch, Material: glowing-orange

            From now on you should only respond using the format.
        '''

    def get_specifics(cls, result: str):
        m = re.match(r"^(?:.*\n)*?.*?Create: (.+?)[,\n ]*Material: (.+?)(?:\n.*)*$", result)
        if m: return (m.group(1), m.group(2))
        else: return result

    def service(cls) -> str:
        return "ShapE"
    
    def spoken(cls, result) -> str:
        object, material = result
        return f"Creating a {material} {object}."
    
    def to_entries(cls, result) -> list[Entry]:
        object, material = result
        return [Entry("prompt", object), Entry("material", material)]