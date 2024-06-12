from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from datastructs.datalist import Entry

class Pipeline:
    def name(cls) -> str: pass
    def service(cls) -> str: pass
    def spoken(cls, result) -> str: pass
    def prompt(self, prompt): pass
    def to_entries(cls, result) -> list[Entry]: return []

class TruePipeline(Pipeline):
    def __init__(self, model: AutoModelForCausalLM, tokenizer: AutoTokenizer) -> None:
        self.pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=self.max_tokens(),
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            repetition_penalty=1.1
        )

    def max_tokens(cls) -> int: pass
    def system_prompt(cls) -> str: pass
    def get_specifics(cls, result): pass

    def build_prompt(cls, prompt: str) -> str:
        return f'''[INST] <<SYS>> { cls.system_prompt() } <</SYS>> {prompt} [/INST]'''

    def prompt(self, prompt: str):
        res: str = self.pipe(self.build_prompt(prompt))[0]['generated_text']
        return self.get_specifics(res.split("[/INST]")[1].strip())
    
class Confused(Pipeline):
    def name(cls): return "CONFUSED"
    def service(cls): return None
    def spoken(cls, result): return result[0]
    def prompt(self, prompt): return ("Sorry I am confused by your prompt, please try again",)

class Terminator(Pipeline):
    def name(cls): return "TERMINATE"
    def service(cls): return None
    def spoken(cls, result): return result[0]
    def prompt(self, prompt): return ("Terminating program",)