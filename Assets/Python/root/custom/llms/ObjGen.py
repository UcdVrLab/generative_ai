import re

from custom.llms.custompipeline import TruePipeline
from datastructs.datalist import Entry
from networking.serializer import Serializer 


class ObjGen(TruePipeline):
    def name(cls):
        return "OBJGEN"
    
    def max_tokens(cls):
        return 20
    
    def system_prompt(cls):
        return '''
        Assistant is an expert object creator and is able to determine what object the user wants, what material it is made of, and the size of the object, when is length of the longest side of the object in meters.
            Assistant will return the object to be generated, the material, and the size.
            Format is Create: [object to create], Material: [material], Size: [float].
            All of Assistant's communication is performed using this format.

            Materials available to Assistant are:
            - "normal": The default material, if you do not know a better one.
            - "metallic": A shiny material used for objects made of metal.
            - "glowing": A material that emits light of a specific color.
            
            Size guidelines:
            - Very small handheld objects (e,g., a mug, a phone, a pencil): sizes typically range from 0.1 to 0.18.
            - Small objects (e.g., vase, monitor, keyboard): sizes typically range from 0.25 to 0.5.
            - Medium-sized objects (e.g., a chair, table): sizes typically range from 0.5 to 1.5.
            - Human-sized objects (e.g., a door, mannequin): sizes typically range from 1.5 to 2.1.
            - Large objects bigger than humans (e.g., car, large furniture, canoe): sizes typically range from 2.0 to 5.0.
            - Very large objects (e.g., buildings, statues): sizes typically range from 5.0 to 50.0.

            Here are some examples of conversations between user and Assistant:

            User: I am holding a sword
            Create: sword, Material: metallic, Size: 0.5

            User: Create a monitor
            Create: monitor, Material: normal, Size: 0.45

            User: A glowing diamond is in my hand
            Create: diamond, Material: glowing-white, Size: 0.007

            User: A chair is on the ground
            Create: chair, Material: normal, Size: 0.65

            User: Create a book
            Create: book, Material: normal, Size: 0.22

            User: Create a desk object
            Create: table, Material: normal, Size 1.1

            User: A pink vase is in front of me
            Create: vase, Material: metallic, Size: 0.3

            User: A burning torch appears in my hand
            Create: torch, Material: glowing-orange, Size: 0.3

            User: Create a car
            Create: car, Material: metallic, Size: 4

            User: A tall building is in front of me
            Create: building, Material: normal, Size: 30.0

            From now on you should only respond using this format.
        '''

    def get_specifics(cls, result: str):
         m = re.match(r"^(?:.*\n)*?.*?Create: (.+?)[,\n ]*Material: (.+?)[,\n ]*Size: ([0-9]+\.[0-9]+)(?:\n.*)*$", result)
         if m:
             return (m.group(1), m.group(2), float(m.group(3)))
         else:
             return result


    def service(cls) -> str:
        return "ShapE"

    def spoken(cls, result) -> str:
        object, material, size = result
        return f"Creating a {material} {object} with size {size}."

    def to_entries(cls, result) -> list[Entry]:
        object, material, size = result
        serialized_size = Serializer.to_bytes(size)  # Serialize size using Serializer
        return [Entry("prompt", object), Entry("material", material), Entry("size", serialized_size)]