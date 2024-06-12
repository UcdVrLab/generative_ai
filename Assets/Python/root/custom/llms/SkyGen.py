from custom.llms.custompipeline import TruePipeline
from datastructs.datalist import Entry
import re

class SkyGen(TruePipeline):
    def name(cls): return "SKYGEN"
    def max_tokens(cls):
        return 70
    def system_prompt(cls):
        return '''
            Assistant is a expert skybox creator and is able to determine what kind of scene the user wishes to see as a skybox.
            Assistant will return a short description of the appearance a skybox that should satisfy the user.
            Format is Description: [skybox to create]
            All of Assistant's communication is performed using this format.

            Here are some examples of conversations between user and Assistant:

            User: I am standing in a forest
            Description: A lush forest surrounds you, towering trees create a canopy above, dappling sunlight on a carpet of moss and fallen leaves.

            User: I have arrived in the throne room
            Description: An opulent throne room, grand pillars support a regal ceiling, ornate tapestries hang, and majestic throne commands attention at the center.

            User: A large cave opens up
            Description: A vast cave unfolds, stalactites hanging like ancient chandeliers, shadows dancing on rough walls.

            From now on you should only respond using the format.
        '''

    def get_specifics(cls, result: str):
        m = re.match(r"^(?:.*\n)*?.*?Description: (.+?)(?:\n.*)*$", result) 
        if m: return (m.group(1),)
        else: return result

    def service(cls) -> str:
        return "StableDiffusion"
    
    def spoken(cls, result) -> str:
        return f"Creating a skybox defined as: {result[0]}"
    
    def to_entries(cls, result) -> list[Entry]:
        modified = f'{result[0]}, Equirectangular, 3D, VR, 360 Image, Beautiful'
        return [Entry("prompt", modified), Entry("width", 1024), Entry("height", 512), Entry("callbacks", 1)]