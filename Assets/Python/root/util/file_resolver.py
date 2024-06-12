from pathlib import Path

def file_from_ancestor(path_to: str, ancestor_name: str = "Assets"):
    path = Path(__file__)
    while path.parent != path:
        path = path.parent
        if path.name == ancestor_name: break
    desired_path = path / path_to
    return desired_path.__str__()