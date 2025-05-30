import re

def parse_complete_prompt(prompt):
    """
    Parses String "Complete: [Set], Objects: [List of Objects]"
    returns Set (string), ObjectList (list).
    """
    match = re.match(r"Complete:\s*(.+?),\s*Objects:\s*\[?(.+?)\]?$", prompt)
    
    if not match:
        print("Error parsing")
    
    set_name = match.group(1).strip()
    object_list_raw = match.group(2).strip()

    object_list = [obj.strip() for obj in object_list_raw.split(',')]
    return set_name, object_list


def parse_coordinates(coord_output: str) -> dict:
    """
    Parses a string like "object (x, y), ..." into a dict: {object: (x, y)}
    """
    obj_coords = {}
    matches = re.findall(r'([\w\s]+)\s*\((\d+),\s*(\d+)\)', coord_output)
    for obj, x, y in matches:
        obj_clean = obj.strip().lower()
        obj_coords[obj_clean] = (int(x), int(y))
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