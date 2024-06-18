from typing import Any
from gtts import gTTS
from io import BytesIO
import miniaudio as mini
import soundfile as sf

from datastructs.datalist import DataList, Entry
from processing.services import Transformation
from processing.processor import SpecialAction
from datastructs.audio import Audio
from datastructs.mesh import Mesh

print("Importing large packages")
import torch
from diffusers import StableDiffusionPipeline,ShapEPipeline,utils
import whisper
import lilfilter
print("Done importing")

print("Starting to load model")
sd_pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", revision="fp16", torch_dtype=torch.float16)
sd_pipe = sd_pipe.to("cuda")
print("Finished loading Stable Diffusion model")

sd_pipe("A cow").images[0].show()

print("Starting to load model")
pipe = ShapEPipeline.from_pretrained("openai/shap-e", torch_dtype=torch.float16, variant="fp16")
pipe = pipe.to("cuda")
print("Finished loading Shap-E model")

mesh_data = pipe("A", guidance_scale=30, num_inference_steps=64, frame_size=256, output_type="mesh").images[0]