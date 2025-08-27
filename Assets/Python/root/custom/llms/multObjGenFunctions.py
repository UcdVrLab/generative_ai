import re
from collections import defaultdict

# def parse_complete_prompt(prompt):
#     """
#     Parses String "Complete: [Set], Objects: [List of Objects]"
#     returns Set (string), ObjectList (list).
#     """
#     match = re.match(r"Complete:\s*(.+?),\s*Objects:\s*\[?(.+?)\]?$", prompt) 
#     ##match = re.search(r"(?:Complete:|Response:)\s*(.+?)\s*Objects:?\s*(.+)$", prompt) TEST

    
#     if not match:
#         print("Error parsing")
#     else:
#         set_name = match.group(1).strip()
#         object_list_raw = match.group(2).strip()

#     object_list = [obj.strip() for obj in object_list_raw.split(',')]
#     return set_name, object_list

def parse_complete_prompt(prompt: str):
    """
    Parses a string to extract a set name and an object list. Reconfigured for more robustness in ther actual system. Edited by Jeric Antony 

    The parsing rules are:
    - Reliably extracts the object list after "Objects:".
    - For the set name:
        - It looks for any word(s) followed by a colon (e.g., "Complete:", "Assistant:").
        - If such a pattern is found, the set name is the FIRST WORD immediately after that colon.
        - If no such "LABEL:" pattern is found before "Objects:", the set name is None.
    - Handles leading/trailing text (chatter) from the LLM.
    - Is case-insensitive for 'Objects:'.
    - Accounts for optional square brackets around the object list.
    - Provides proper error handling if the "Objects: ..." pattern isn't found.
    """

    pattern = r"^(?:.*?)(?:(?:[\w\s]+?):\s*(.+?))?,\s*Objects:\s*\[?(.*?)\]?(?:$|\n.*)"
    
    # Use re.search to find the pattern anywhere in the string
    # Use re.IGNORECASE for robustness on "Objects:"
    # Use re.DOTALL to allow '.' to match newlines (if LLM output spans lines)
    match = re.search(pattern, prompt, re.IGNORECASE | re.DOTALL)

    if not match:
        print(f"Error parsing prompt: Could not find 'Objects: [list]' pattern in '{prompt}'")
        return None, None # Return None for both if the core pattern isn't found

    # Group 1 is the full text after the colon, if the LABEL: part was matched.
    # Group 2 is the raw object list.
    set_name_full_phrase = match.group(1)
    object_list_raw = match.group(2).strip()

    # Process Set Name
    set_name = set_name_full_phrase

    # Process Object List 
    object_list = []
    if object_list_raw:
        object_list = [obj.strip() for obj in object_list_raw.split(',')]
        # Filter out any empty strings that might result from extra commas (e.g., "a,,b")
        object_list = [obj for obj in object_list if obj]


    return set_name, object_list




def parse_coordinates(coord_output: str) -> dict:
    """
    Parses a string like "object (x, y), ..." into a dict: {object: (x, y)}
    """
    obj_coords = {}
    matches = re.findall(r'([\w\s]+)\s*\((\d+),\s*(\d+)\)', coord_output)
    for obj, x, z in matches:
        obj_clean = obj.strip().lower()
        obj_coords[obj_clean] = (int(x), int(z))
    return obj_coords


def place_objects_on_grid(obj_coords, grid_size=20):
    """
    Places objects on a 2D grid based on parsed coordinates.
    Uses (x, y) -> grid[y][x], where (0,0) is top-left.
    """
    grid = [["" for _ in range(grid_size)] for _ in range(grid_size)]

    for obj, (x, y) in obj_coords.items():
        if 0 <= x < grid_size and 0 <= y < grid_size:
            if grid[y][x] == "":
                grid[y][x] = obj
            else:
                print(f"Warning: Cell ({x},{y}) already occupied by {grid[y][x]}. Cannot place {obj}.")
        else:
            print(f"Warning: {obj} has invalid coordinates ({x},{y}). Skipping.")
    return grid


def print_grid(grid):
    """
    Prints the grid in a human-readable way.
    """
    for row in grid:
        row_str = ""
        for cell in row:
            if cell == "":
                row_str += ". "
            else:
                row_str += f"{cell[0].upper()} "
        print(row_str)


def find_duplicate_coords(coord_dict):
    """
    Made by Jeric Antony 20/08/25
    Parses the dict and creates a default dict with coords as keys that have multiple objects
    Returns a list of string to be given to collision resolver
    """
    duplicates = defaultdict(list)
    for obj_name, coord in coord_dict.items():
        duplicates[coord].append(obj_name)

    for key in list(duplicates.keys()):
        if len(duplicates[key]) < 2:
            del duplicates[key]

    duplicates_string_list = [f"{key}: {value}" for key, value in duplicates.items()]

    return duplicates_string_list

def parse_coordinates_3D(coord_output: str) -> dict:
    """
    Made by Jeric Antony 20/08/25
    Parses a string like "object (x, y, z), ..." into a dict: {object: (x, y, z)}
    Also includes floats
    """
    obj_coords = {}
    matches = re.findall(r'([\w\s]+) \((\d{1,2}(?:\.\d{1})?), (\d{1,2}(?:\.\d{1})?), (\d{1,2}(?:\.\d{1})?)\)', coord_output)
    for obj, x, y, z  in matches:
        obj_clean = obj.strip().lower()
        obj_coords[obj_clean] = (float(x), float(y), float(z))
    return obj_coords

def coords_to_3D(coords_dict):
    """
    Made by Jeric Antony 20/08/25
    Parses the dict and converts any 2d coordinate into a 3d coordinate by a default 0.5 y coordinate
    """
    for obj, coord in coords_dict.items():
        if len(coord) == 2:
            coords_dict[obj] = (float(coord[0]), 0.5, float(coord[1]))


