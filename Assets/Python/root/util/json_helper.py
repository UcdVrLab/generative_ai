import json
from util.file_resolver import file_from_ancestor

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in '{file_path}': {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_token(name):
    try:
        json = read_json_file(file_from_ancestor(f"Config/tokens/{name}.json"))
        return json["token"]
    except Exception as e:
        print("Could not obtain token due to exception")
        print(e)
