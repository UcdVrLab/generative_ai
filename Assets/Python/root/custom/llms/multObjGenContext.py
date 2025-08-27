import re
from collections import defaultdict
from typing import Union, List

objlist_context = '''
Assistant is an expert object creator and is able to generate multiple objects at once. For each object, it determines what key objects are included in the prompt.
Assistant will return the list of objects to be generated.

- A maximum of 7 objects will be generated per request.
- No order is necessary, only relevancy to the prompt.
- If an object by itself is unclear, add a short description to clarify, e.g., X-wing -> X-wing spaceship, Luger -> Luger pistol.

Format is Complete: [Set to complete], Objects: [list of objects].
All of Assistant's communication is performed using this format.

Here are some examples of conversations between user and Assistant:

User: Complete a pc setup
Complete: pc setup, Objects: pc, desk, monitor, mouse, keyboard, office chair

User: Complete a living room space
Complete: living room space, Objects: sofa, coffee table, TV, TV stand, bookshelf, lamp, rug

User: Complete a home gym space with a dumbell rack
Complete: home gym space, Objects: yoga mat, dumbells, weights, bench, treadmill, dumbell rack

User: Complete a garden setup
Complete: garden setup, Objects: flowerbed, bushes, trees, gardening tools, watering can, garden bench, flowerpots with flowers

User: Complete a bedroom setup with a chair
Complete: bedroom setup, Objects: bed, nightstand, lamp, dresser, wardrobe, chair

User: Complete a set of PC Parts
Complete: PC Parts, Objects: PC case, GPU, CPU, motherboard, PSU, RAM

User: Complete a toolkit set with a wrench on a table
Complete: toolkit set, Objects: hammer, screwdriver, pliers, wrench, electric tape, DIY table, drill, nails

User: Complete a camping setup
Complete: camping setup, Objects: tent, sleeping bag, campfire, lantern, backpack, camp stove, folding chair, bag of marshmellows

User: Complete a first aid kit in a box
Complete: first aid kit, Objects: bandages, antiseptic, gauze, thermometer, scissors, tweezers, medical tape, gloves, kitbox

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
You will be given a list of objects that need to be placed relative to one another in a 3D space using certain defined relations.
You will be responsible for defining the relations between objects; 2 objects at a time.

Input format:
- You will receive the objects in the form [object1, object2, object3, ...].

Here are the relations and their defintions:
- Only use the relations: "infrontof", "totherightof", "totheleftof", "ontopof".
- "infrontof": objectA infrontof objectB means that objectA should face or be in front of objectB
- "totherightof": objectA totherightof objectB means that objectA should be beside and to the right of objectB
- "totheleftof": objectA totheleftof objectB means that objectA should be beside and to the left of objectB
- "ontopof": objectA ontopof objectB means that objectA should lie on or hover above objectB


Guidelines:
- Each relation must be between two objects.
- I will use your guideline to arrange the objects *iteratively*, so please start with an anchor object which doesn't depend on the other objects, and place that with its most obvious relation
- Place the larger objects first.
- The latter objects could only depend on the former objects. i.e. every relation apart from the first relation should use a previously used object, must link together
- Chairs must be placed near to the table/desk
- Keep the relations simple and logical based on real-world assumptions.
- Do NOT invent new objects.
- Do NOT add extra commentary or explanation.
- If no obvious relation is possible, simply skip it
- Adhere to the guidelines and output format strictly
- Only output the relations in the format:

[Object placeholder] infrontof [Object placeholder], [Object placeholder] totherightof [Object placeholder], [Object placeholder] totheleftof [Object placeholder], etc 

All of Assistant's communication is performed using this format.

Your output MUST be a single line of comma-separated relations. DO NOT ask questions, offer explanations, or provide any commentary whatsoever.

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

Input: [remote, TV, couch, blanket]
Output: remote infrontof TV, couch infrontof remote, blanket ontopof couch

Input: [glasses, table, mug, newspaper]
Output: glasses ontopof newspaper, mug totheleftof glasses, newspaper infrontof table

Input: [shoes, mat, door, coat rack]
Output: shoes infrontof door, mat infrontof shoes, coat rack totherightof door

Input: [keys, bowl, table, fruit]
Output: keys ontopof bowl, bowl infrontof table, fruit totheleftof bowl

Input: [chair, table, vase, placemat]
Output: chair infrontof table, vase ontopof table, placemat infrontof vase

<End of Examples>

Always follow this structure exactly.
Do not add any output extra to this

Generate output now, strictly adhering to the format.
'''

class RelationalMappingAssistant:
    def __init__(self, pipeline, context):
        self.pipeline = pipeline
        self.context = context.strip()

    def process_request(self, object_list: list):
        objects_formatted = "[" + ", ".join(object_list) + "]"
        print(objects_formatted)
        full_prompt = f"{self.context}\n\nInput: {objects_formatted}\nOutput:\n"
        response = self.pipeline(full_prompt)[0]['generated_text']

        split_response = response.split(f"Input: {objects_formatted}\nOutput:\n", 1)
        if len(split_response) > 1:
            answer = split_response[1].strip()
            print(answer)
            #answerList = [obj.strip() for obj in answer.split(',')]
            answerList = re.split(r'[,|\n]', answer)
            return answerList
        return response.strip()
    

grid_context = '''
You are a spatial layout planner for a 20x20 virtual grid. Your job is to assign (x, y) coordinates to a set of objects based on their relative spatial relationships.
Each relationship describes how one object is placed in relation to another. Use these relations to infer direction and appropriate distance between objects.

Your goals:
- Start by placing only the first object at (10, 10), use this as an anchor point to place all other objects around using the relational map.
- Use logical spacing:
- Avoid placing objects small objects too far apart (2-3 units) unless absolutely necessary.
- Place large objects further apart to avoid collisions unless they need to collide (3-6) units.
- Maintain directional accuracy:
    - "infrontof" → object is above (lower Y)
    - "totherightof" → object is to the right (higher X)
    - "totheleftof" → object is to the left (lower X)
- Choose meaningful distances (e.g., 1–5 units) to separate objects clearly.
- You may have some (but not all) items that share coordinates like items which are 'ontopof' another.
- Never rename or modify the object names.
- Keep all coordinates within the 0–19 grid limits.

Output Format:
- Return each object and its coordinates as: `object (x, y)`
- Separate with commas on one line only.
- No extra commentary or explanation.

Examples:

Input: keyboard infrontof monitor, mouse totherightof keyboard, pc totheleftof monitor  
Output: keyboard (10, 10), monitor (10, 11), mouse (11, 10), pc (6, 12)

Input: remote infrontof TV, couch infrontof remote, blanket ontopof couch
Output: remote (10, 10), TV (10, 12), couch (10, 8), blanket (10, 8)

Input: glasses ontopof newspaper, mug totheleftof glasses, newspaper infrontof table
Output: glasses (10, 10), newspaper (10, 10), mug (8, 10), table (10, 12)

Input: shoes infrontof door, mat infrontof shoes, coat rack totherightof door
Output: shoes (10, 10), door (10, 12), mat (10, 8), coat rack (12, 12)

Input: keys ontopof bowl, bowl infrontof table, fruit totheleftof bowl
Output: keys (10, 10), bowl (10, 10), table (10, 12), fruit (8, 10)

<End of Examples>

Always follow this exact output format.
'''



relation_scaling_context = '''
You are an helper for a grid placement system for multiple objects. You get to choose the distance based on size to separate two objects.
- These are the types of relations yopu will decide a separation value for:
    - "infrontof" → object is above (lower Y)
    - "totherightof" → object is to the right (higher X)
    - "totheleftof" → object is to the left (lower X)
All you need to do is choose a distance that should place the new object in the correct place based on the spatial relation and the approximate size.
Assume the appropriate vector direction is already chosen, based on size and logical accuracy, determine the distance separation for the two objects with regard to the inbetween relation

Guidelines:
- Use logical spacing (e.g. smaller objects need less separation space than larger objects)
- Small Items: Choose increments of +/- 0.2 distances for small items that need to be close together
    - Avoid placing objects small objects too far apart (2-3 units) unless absolutely necessary.
- Large Items: Choose only increments of 1.0 or 0.5 distances for large items that require separation
    - Place large objects further apart to avoid collisions unless they need to collide (3-6) units.
- Choose meaningful distances (e.g., 1–5 units) to separate objects clearly.
- Keep all distances within the 0–19 grid limits.
- Only output the distance number
- Do not output any other information at all

Examples:
Input: chair infrontof desk
Output: 1.0

Input: book totherightof cup
Output: 0.4

Input: car totheleft of tree
Output: 2.5

Input: fork totherightof plate
Output: 0.5

Input: sofa infrontof TV
Output: 1.5

Input: phone totheleftof book
Output: 0.2

Input: keyboard infrontof monitor
Output: 0.4

Input: cat totherightof dog
Output: 0.6

<End of Examples>
Always follow this structure exactly.
Do not add any output extra to this

Generate output now, strictly adhering to the format.

'''

class GridPlacementAssistant:
    def __init__(self, pipeline, context):
        self.pipeline = pipeline
        self.context = context.strip()
        self.vectors = {# Pre-defined directional vectors
            'infrontof': (0, -1),
            'totherightof': (1, 0),
            'totheleftof': (-1, 0),
            'ontopof': (0, 0) # On top doesn't change XZ
        }
        self.relation_scaling_context = relation_scaling_context
        

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
    

    '''
    Made by Jeric Antony 20/08/25
    Anchor based coordinate grid system instead of generating all the coordinates at once. More accurate with spatial relations than previous method
    but takes more time as ai provides a separation distance for each relation
    '''
    def grid_relation_alignment(self, relations: list):
        anchor = False
        obj_coords = {}
        for rel in relations:
            #print(f"\n{rel}")
            invert_vector = False
            pattern = "^(.+?)\s+(infrontof|totherightof|totheleftof|ontopof)\s+(.+?)$"
            match = re.match(pattern, rel)
            if match:
                obj1 = match.group(1).strip().lower()    # Stripping whitespace is good practice
                relation = match.group(2)
                obj2 = match.group(3).strip().lower()
            else:
                #print("\nNo match found")
                continue

            if not anchor:
                obj_coords[obj2] = (10, 10) # Central anchor point
                anchor = True


            if obj2 not in obj_coords:
                if obj1 not in obj_coords: #2 new objs
                    if anchor:
                        obj_coords[obj2] = (10, 10) # new mini anchor point/temp
                    obj = obj2
                    obj_new = obj1
                else:                 #1 new obj, obj2
                    obj = obj1
                    obj_new = obj2
                    invert_vector = True
            elif obj1 not in obj_coords: #1 new obj, obj 1
                obj = obj2
                obj_new = obj1
            else:                  #0 new objs
                continue



            # Special case for 'ontopof' - share the same XY coords
            if relation == 'ontopof':
                new_x, new_y = obj_coords[obj]
            else:
                # Get the initial vector and AI-based adjustment
                base_x, base_y = self.vectors[relation]
                if invert_vector:
                    base_x *= -1
                    base_y *= -1

                adjustment = self.request_relation_scaling(rel)
                
                # Calculate the new coordinates
                new_x = obj_coords[obj][0] + (base_x * adjustment)
                new_y = obj_coords[obj][1] + (base_y * adjustment)
                
            
            obj_coords[obj_new] = (new_x, new_y)
            #print(f"\n\t{relation}, {obj_coords}")
        
        return obj_coords
    
    '''
    LLM Scaling Factor for Relation - Made by Jeric Antony 20/08/25
    '''
    def request_relation_scaling(self, relation: str):
        full_prompt = f"{self.relation_scaling_context}\n\nInput:{relation}\nOutput:\n"
        response = self.pipeline(full_prompt, max_new_tokens=100)[0]['generated_text']

        split_response = response.split(full_prompt, 1)
        if len(split_response) > 1:
            answer = split_response[1].strip()
        else:
            answer = response.strip()


        scalar = 1
        match = re.search("\d+(\.\d+)?", answer)
        if match:
            scalar_str = match.group(0)
            try:
                scalar = float(scalar_str)
            except ValueError:
                scalar = 1

        print(scalar)
        return scalar





grid_resolver_context = '''
You are a spatial layout collision resolver for a 20x20x20 virtual grid. Your job is to give (x, y, z) coordinates to a set of objects which are currently overlapping in (x, z) space and space them out based on their relative spatial and size relationships.

Your goals:
- For each coordinate using the current relations find the relation between the two specified objects such as 'infrontof', 'behind' , 'totherightof' , 'totheleftof', 'ontopof'.
- If there is no relation already then DECIDE yourself where objects need to be in relation with each other using 'infrontof', 'behind' , 'totherightof' , 'totheleftof', 'ontopof'.
- Maintain logical and visual accuracy for your spacial relation decision
- Use these guidelines and examples to influence how logical the ouput should be

- If using 'infrontof' or 'behind' then offset the z coordinates (e.g. lower z  for 'infront', higher z for 'behind')
- If using 'totherightof' or 'totheleftof' then offset the x coordinates (e.g. higher x for 'totherightof', lower x for 'totheleftof')
- For each coordinate (only if decided) decide an offset in the x and z coordinates for objects using increments of +/- 0.2
- Use logical spacing based on size (e.g. smaller objects need less separation space than larger objects)

- If using 'ontopof' decide where objects in the same space should be vertically (e.g. above/below, give each a y value)
- Choose meaningful vertical distances (e.g. using increments of +/- 0.2 units for small objects and +/- 0.5 for medium objects and +/- 1.0 to 1.5 for very large objects) to separate objects clearly.
- Use 0.5 as a default y coordinate if y coordinate is not changed

- **Prioritize spreading objects horizontally using x/z offsets before stacking vertically (e.g. large objects need to be seperated horizontally)**
- **When resolving collisions for 3 or more objects, you must utilize x/z offsets for at least one object to ensure horizontal separation, even if some vertical stacking occurs.**
- Never rename or modify the object names.
- Keep all coordinates within the 0–19 grid limits.

Output Format:
- Return each object and its coordinates as: `object (x, y, z)`
- Separate with commas on one line only.
- No extra commentary or explanation.

Examples:

Current Relational Map: ['bed infrontof dresser', 'nightstand totherightof bed', 'lamp ontopof nightstand']
Input:
(10, 12): ['nightstand', 'lamp']
Output:
nightstand (10, 0.5, 12), lamp (10, 0.5, 12)

Current Relational Map: ['apple ontopof bowl', 'apple totherightof banana', 'pear totherightof apple']
Input:
(1, 2): ['apple', 'banana']
Output: 
apple (1.2, 0.5, 2), banana (0.8, 0.5, 2),

Current Relational Map: ['monitor ontopof desk', 'keyboard infrontof monitor', 'chair infrontof desk']
Input:
(7, 7): ['desk', 'monitor', 'keyboard', 'cup', 'chair']
Output: 
desk (7, 0.5, 7), monitor (7, 1.0, 7), keyboard (7, 1.0, 6.6), cup (6.8, 1.0, 6.6), chair (7, 0.5, 6.0)

Current Relational Map: ['car totherightof tree', 'tree behind bush', 'flower infrontof bush', 'dog totheleft of flower']
Input:
(2, 10): ['tree', 'bush', 'flower']
Output: 
tree (2, 0.5, 10), bush (2, 0.5, 9.8), flower (2, 0.5, 9.6)

Current Relational Map: ['vase ontopof drawer']
Input:
(19, 19): ['drawer', 'vase', 'candlestick']
Output: 
drawer (19, 0.5, 19), vase (19, 0.7, 19), candlestick (19.2, 0.7, 19)


<End of Examples>

Always follow this exact output format.
'''


'''
Made by Jeric Antony 20/08/25
Batch processes any grid collision and addes either horizontal or vertical separation based on spatial relation. Drastically improved accuracy to MOG pipeline. 
Batch processing speeds it up and doesnt add significant delay to MOG pipeline
'''
class GridCollisionAssistant:
    def __init__(self, pipeline, context):
        self.pipeline = pipeline
        self.context = context.strip()

    def process_request(self, inputs: Union[str, List[str]], relations: list)-> Union[str, List[str]]:
        """
        Processes one or more collision resolution requests in a batched manner.
        """
        is_single_input = isinstance(inputs, str)
        prompts_to_process = [inputs] if is_single_input else inputs

        full_prompts = []
        for individual_input in prompts_to_process:
            full_prompts.append(f"{self.context}\n\nCurrent Relational Map:{relations}\nInput:\n{individual_input}\nOutput:\n")

        batch_responses = self.pipeline(full_prompts, max_new_tokens=100)

        outputs_raw = []
        for i, response_single_prompt in enumerate(batch_responses):
            response = response_single_prompt[0]['generated_text']

            original_prompt_for_split = full_prompts[i]

            # Most of the time gives output we want + extra print
            # We extract only the lines that match "object (x, y)"
            split_response = response.split(original_prompt_for_split, 1)
            if len(split_response) > 1:
                answer = split_response[1].strip()
            else:
                answer = response.strip()
            matches = re.findall(r'\b[\w\s]+ \(\d{1,2}(?:\.\d{1})?, \d{1,2}(?:\.\d{1})?, \d{1,2}(?:\.\d{1})?\)', answer)
            outputs_raw.append(", ".join(matches))
        
        return outputs_raw[0] if is_single_input else outputs_raw
    