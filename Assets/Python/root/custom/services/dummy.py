import os
from typing import Any

from processing.processor import SpecialAction
from datastructs.datalist import DataList, Entry
from processing.services import Transformation
from datastructs.audio import Audio
from datastructs.mesh import Mesh
from util.file_resolver import file_from_ancestor

from PIL import Image
import numpy as np

def add_noise(image, amount):
    output = np.copy(np.array(image))
    # add salt
    nb_salt = np.ceil(amount * output.size * 0.5)
    coords = [np.random.randint(0, i - 1, int(nb_salt)) for i in output.shape]
    output[tuple(coords)] = np.random.randint(200, 256, int(nb_salt))
    # add pepper
    nb_pepper = np.ceil(amount* output.size * 0.5)
    coords = [np.random.randint(0, i - 1, int(nb_pepper)) for i in output.shape]
    output[tuple(coords)] = np.random.randint(0, 56, int(nb_pepper))
    return Image.fromarray(output)


class StableDiffusion(Transformation):
    def process(self, dl: DataList) -> DataList:
        dl.pop_content_by_message('prompt')
        dl.pop_content_get_data_by_message('width')
        dl.pop_content_get_data_by_message('height')
        file_name = file_from_ancestor(f"StreamingAssets/360.png")
        image = Image.open(file_name).convert('RGB')
        for i in range(0, 50):
            noise = -np.log((i + 1) / 50) / 5
            copy = dl.shallow_copy()
            copy.add_content(Entry('diffused image', add_noise(image, noise)))
            self.give(copy)
        return SpecialAction.NOTHING
    
class Whisper(Transformation):
    def process(self, dl: DataList) -> DataList:
        audio: Audio = dl.pop_content_of_type('audio').data
        dl.add_content(Entry('transcribed text', "Gibberish..."))
        return dl
    
class ShapE(Transformation):
    def process(self, dl: DataList) -> DataList:
        dl.pop_content_by_message('prompt')
        file_name = file_from_ancestor(f"StreamingAssets/mesh.bin")
        with open(file_name, mode="rb") as f:
            mesh_data = f.read()
        dl.add_content(Entry('an umbrella', Mesh.from_bytes(mesh_data)))
        return dl