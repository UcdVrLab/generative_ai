import re

objlist_context = '''
Assistant is an expert object creator and is able to generate multiple objects at once. For each object, it determines what key objects are included in the prompt.
Assistant will return the list of objects to be generated. A maximum of 10 objects will be generated per request.
No order is necessary, only relevancy to the prompt.
If an object by itself is unclear, add a short description to clarify, e.g., X-wing -> X-wing spaceship, Luger -> Luger pistol.
Format is Complete: [Set to complete], Objects: [list of objects].
All of Assistant's communication is performed using this format.

Here are some examples of conversations between user and Assistant:

User: Complete a pc setup
Complete: pc setup, Objects: pc, desk, monitor, mouse, keyboard, office chair

User: Complete a living room space
Complete: living room space, Objects: sofa, coffee table, TV, TV stand, bookshelf, lamp, rug

User: Complete a home gym space
Complete: home gym space, Objects: yoga mat, dumbells, weights, bench, treadmill

User: Complete a garden setup
Complete: garden setup, Objects: flowerbed, bushes, trees, gardening tools, watering can, garden bench, flowerpots with flowers

User: Complete a bedroom setup
Complete: bedroom setup, Objects: bed, nightstand, lamp, dresser, wardrobe, chair

User: Complete a set of PC Parts
Complete: PC Parts, Objects: PC case, GPU, CPU, motherboard, PSU, RAM

User: Complete a toolkit set
Complete: toolkit set, Objects: hammer, screwdriver, pliers, wrench, electric tape, cardboard knife, drill, nails

User: Complete a camping setup
Complete: camping setup, Objects: tent, sleeping bag, campfire, lantern, backpack, camp stove, folding chair, bag of marshmellows

User: Complete a first aid kit
Complete: first aid kit, Objects: bandages, antiseptic, gauze, thermometer, scissors, tweezers, medical tape, gloves

User: Complete a set of orchestra instruments
Complete: orchestra instruments, Objects: violin, cello, trumpet, trombone, flute, clarinet, saxophone, drums, piano

User: Complete a set of different dishes
Complete: different dishes, Objects: spaghetti, pizza, salad, sushi, lasagna, steak, chicken wings, soup, chocolate cake

User: Complete an array of WW2 weapons
Complete: WW2 weapons, Objects: M1 Garand rifle, Kar98k rifle, Thompson submachine gun, MP40 submachine gun, Sten gun, Luger pistol, grenade, pipe bomb

User: Complete an array of Star Wars spaceships
Complete: Star Wars spaceships, Objects: X-wing spaceship, Y-wing spaceship, TIE fighter spaceship, Millennium Falcon spaceship, Star Destroyer spaceship

From now on you should only respond using this format.
'''


class ObjectListAssistant:
    def __init__(self, pipeline, context):
        self.pipeline = pipeline
        self.context = objlist_context.strip()

    def process_request(self, prompt: str):
        full_prompt = f"{self.context}\nUser: {prompt}\n"
        response = self.pipeline(full_prompt)[0]['generated_text']

        split_response = response.split(f"User: {prompt}\n", 1)
        if len(split_response) > 1:
            answer = split_response[1].strip().split('\n')[0]
            return answer
        return response.strip()




relational_context = '''
You are a spatial layout assistant. 
You will be given a list of objects that need to be placed relative to one another in a 2D space.
You will be responsible for defining the relations between objects.

Input format:
- You will receive the objects in the form [object1, object2, object3, ...].

Rules:
- Only use the relations: "infrontof", "totherightof", "totheleftof".
- Each relation must be between two objects.
- One relation per line.
- Keep the relations simple and logical based on real-world assumptions.
- Do not invent new objects.
- Do not add extra commentary or explanation.
- Only output the relations in the format:

objectA infrontof objectB
objectA totherightof objectB
objectA totheleftof objectB

If no obvious relation is possible, simply skip it.

<Examples>

Input: [keyboard, monitor, mouse, pc]
Output: keyboard infrontof monitor, mouse totherightof keyboard, pc totheleftof monitor

Input: [book, lamp, notebook]
Output: book infrontof lamp, notebook totherightof book

Input: [cup, plate, fork, knife]
Output: cup infrontof plate, fork totherightof plate, knife totherightof fork

Input: [sofa, coffee table, TV, bookshelf]
Output: sofa infrontof TV, coffee table infrontof sofa, bookshelf totherightof TV

Input: [bed, nightstand, lamp, dresser]
Output: bed infrontof dresser, nightstand totherightof bed, lamp ontopof nightstand

Input: [phone, laptop, charger, headphones]
Output: phone totherightof laptop, charger totherightof phone, headphones totherightof charger

<End of Examples>

Always follow this structure exactly.
'''

class RelationalMappingAssistant:
    def __init__(self, pipeline, context):
        self.pipeline = pipeline
        self.context = context.strip()

    def process_request(self, object_list: list):
        objects_formatted = "[" + ", ".join(object_list) + "]"
        full_prompt = f"{self.context}\n\nInput: {objects_formatted}\nOutput:\n"
        response = self.pipeline(full_prompt)[0]['generated_text']

        split_response = response.split(f"Input: {objects_formatted}\nOutput:\n", 1)
        if len(split_response) > 1:
            answer = split_response[1].strip()
            return answer
        return response.strip()
    

grid_context = '''
You are a spatial layout planner for a 20x20 virtual grid. Your job is to assign (x, y) coordinates to a set of objects based on their relative spatial relationships.
Each relationship describes how one object is placed in relation to another. Use these relations to infer direction and appropriate distance between objects.

Your goals:
- Start by placing the first object at (10, 10).
- Use logical spacing — avoid placing objects just 1 unit apart unless absolutely necessary.
- Maintain directional accuracy:
    - "infrontof" → object is above (lower Y)
    - "totherightof" → object is to the right (higher X)
    - "totheleftof" → object is to the left (lower X)
- Choose meaningful distances (e.g., 1–5 units) to separate objects clearly.
- No duplicate positions.
- Never rename or modify the object names.
- Keep all coordinates within the 0–19 grid limits.

Output Format:
- Return each object and its coordinates as: `object (x, y)`
- Separate with commas on one line only.
- No extra commentary or explanation.

Example:

Input:  
keyboard infrontof monitor  
mouse totherightof keyboard  
pc totheleftof monitor  

Output:  
keyboard (10, 10), monitor (10, 12), mouse (12, 10), pc (6, 12)

Always follow this exact output format.
'''



class GridPlacementAssistant:
    def __init__(self, pipeline, context):
        self.pipeline = pipeline
        self.context = context.strip()

    def process_request(self, relations: list):
        relations_formatted = "\n".join(relations)
        full_prompt = f"{self.context}\n\nInput:\n{relations_formatted}\n\nOutput:\n"
        response = self.pipeline(full_prompt, max_new_tokens=100)[0]['generated_text']

        # Most of the time gives output we want + extra print
        # We extract only the lines that match "object (x, y)"
        split_response = response.split(full_prompt, 1)
        if len(split_response) > 1:
            answer = split_response[1].strip()
        else:
            answer = response.strip()
        matches = re.findall(r'\b[\w\s]+ \(\d{1,2}, \d{1,2}\)', answer)
        return ", ".join(matches)