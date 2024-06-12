from typing import Any
from gtts import gTTS
from io import BytesIO
import miniaudio as mini
import soundfile as sf
from PIL import Image


from datastructs.datalist import DataList, Entry
from processing.services import Transformation
from processing.processor import SpecialAction
from datastructs.audio import Audio
from datastructs.mesh import Mesh

print("Importing large packages")
import torch
from diffusers import StableDiffusionPipeline,ShapEPipeline
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import lilfilter
print("Done importing")

import matplotlib.pyplot as plt

sd_pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", revision="fp16", torch_dtype=torch.float16)
sd_pipe = sd_pipe.to("cuda")

class StableDiffusion(Transformation):
    def setup(self):
        print("Starting to load Stable Diffusion model")
        # self.send_special(self.create_special_dl(DataList(), Entry("log", f"Stable Diffusion Initializing"), "Debugger"))
        
        print("Finished loading Stable Diffusion model")
        self.send_special(self.create_special_dl(DataList(), Entry("log", f"Stable Diffusion Loaded"), "Debugger"))

    def process(self, datalist: DataList) -> DataList:
        prompt: str = datalist.pop_content_by_message('prompt').data
        width: int = datalist.pop_content_get_data_by_message('width')
        height: int = datalist.pop_content_get_data_by_message('height')
        callbacks: int = datalist.pop_content_get_data_by_message('callbacks')
        if not width: width = 512
        if not height: height = 512

        def callback(step, t, latents):
            with torch.no_grad():
                latents = 1 / 0.18215 * latents
                image = sd_pipe.vae.decode(latents).sample
                image = (image / 2 + 0.5).clamp(0, 1)
                image = image.cpu().permute(0, 2, 3, 1).float().numpy()
                image = sd_pipe.numpy_to_pil(image)
                flipped = image[0].transpose(Image.FLIP_TOP_BOTTOM)
                copy = datalist.shallow_copy()
                copy.add_content(Entry('diffused image', flipped))
                self.give(copy)
        while True: 
            try:
                if callbacks: sd_pipe(prompt, height=height, width=width, callback=callback, callback_steps=1)
                else: 
                    im = sd_pipe(prompt, height=height, width=width).images[0].transpose(Image.FLIP_TOP_BOTTOM)
                    copy = datalist.shallow_copy()
                    copy.add_content(Entry('diffused image', im))
                    return copy
                return SpecialAction.NOTHING
            except Exception:
                print("A weird exception occured, trying again")

processor = AutoProcessor.from_pretrained("openai/whisper-tiny")
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    "openai/whisper-tiny", torch_dtype=torch.float16, low_cpu_mem_usage=True, use_safetensors=True
).to("cuda")
resampler = lilfilter.Resampler(44100, 16000, torch.float32)
wpipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=128,
    chunk_length_s=30,
    batch_size=1,
    return_timestamps=True,
    torch_dtype=torch.float16,
    device="cuda",
)
    
class Whisper(Transformation):
    def setup(self):
        print("Starting to load Whisper model")
        # self.send_special(self.create_special_dl(DataList(), Entry("log", f"Whisper Initializing"), "Debugger"))
        print("Finished loading Whisper model")
        self.send_special(self.create_special_dl(DataList(), Entry("log", f"Whisper Loaded"), "Debugger"))

    def process(self, dl: DataList) -> DataList:
        audio: Audio = dl.pop_content_by_message('audio').data
        resampledData = resampler.resample(torch.from_numpy(audio.data.reshape([1, -1]))).numpy().reshape([-1])
        parsed = wpipe(resampledData)["text"] 
        dl.add_content(Entry('prompt', parsed))
        self.send_special(self.create_special_dl(DataList(), Entry("log", f"User: {parsed}"), "Debugger"))
        return dl
    
pipe = ShapEPipeline.from_pretrained("openai/shap-e", torch_dtype=torch.float16, variant="fp16")
pipe = pipe.to("cuda")

class ShapE(Transformation):
    def setup(self):
        print("Starting to load Shap-E model")
        # self.send_special(self.create_special_dl(DataList(), Entry("log", f"Shap-E Initializing"), "Debugger"))
        
        print("Finished loading Shap-E model")
        self.send_special(self.create_special_dl(DataList(), Entry("log", f"Shap-E Loaded"), "Debugger"))

    def process(self, dl: DataList) -> DataList:
        prompt: str = dl.pop_content_by_message('prompt').data
        mesh_data = pipe(prompt, guidance_scale=30, num_inference_steps=64, frame_size=256, output_type="mesh").images[0]
        try:
            self.send_special(self.create_special_dl(dl, Entry("log", f"System: Mesh created"), "Debugger"))
            dl.add_content(Entry(prompt, Mesh(mesh_data)))
            return dl
        except: 
            print("Mesh had too many vertices")
            self.send_special(self.create_special_dl(dl, Entry("message", f"Failed to create mesh: {prompt}, too many vertices."), "GTTS"))
            self.send_special(self.create_special_dl(dl, Entry("log", f"System: Failure to create mesh"), "Debugger"))
            return SpecialAction.NOTHING

class GTTS(Transformation):
    def process(self, dl: DataList) -> DataList:
        msg: str = dl.pop_content_by_message("message").data
        gtts = gTTS(text=msg, lang='en') 
        mp3 = BytesIO()
        wav = BytesIO()
        gtts.write_to_fp(mp3)
        decoded = mini.mp3_read_s16(mp3.getvalue())
        sf.write(wav, decoded.samples, decoded.sample_rate, format='WAV')
        dl.add_content(Entry("audio message", Audio(wav.getvalue())))
        return dl