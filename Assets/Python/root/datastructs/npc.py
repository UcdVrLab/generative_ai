from queue import Queue
from transformers import pipeline

class Buffer:
    def __init__(self, size: int) -> None:
        self.queue = Queue(size)

    def add(self, item):
        if self.queue.full(): self.queue.get()
        self.queue.put(item)
    
    def all(self):
        return [i for i in self.queue.queue]
    
    def last(self):
        return self.all()[-1]
    def previous(self):
        return '\n'.join(self.all()[:-1]) 
    
class NPC:
    def __init__(self, id, name, desc, model, tokenizer) -> None:
        self.id = id
        self.model = model
        self.tokenizer = tokenizer
        self.name = name
        self.desc = desc
        self.memory = Buffer(20)
        self.chat = pipeline(
            "text-generation", model=model, tokenizer=tokenizer, max_new_tokens=128, do_sample=True, temperature=0.7, top_p=0.95, top_k=40, repetition_penalty=1.5
        )
        self.initiative = pipeline(
            "text-generation", model=model, tokenizer=tokenizer, max_new_tokens=10, do_sample=True, temperature=0.7, top_p=0.95, top_k=40, repetition_penalty=1.5
        )
        
    #called on NPCs in earshot
    def hear(self, message):
        self.memory.add(message)
        return message

    def test_initiative(self) -> bool:
        answer: str = self.initiative(self.initiative_template())[0]['generated_text'].split("[/INST]\n")[1].strip()
        return "YES" in answer.upper()
        
    def respond(self) -> str:
        if self.test_initiative():
            response = self.chat(self.chat_template())[0]['generated_text'].split("[/INST]\n")[1].split("\n")[0].strip()
            self.memory.add(response)
            return response

    def chat_template(self):
        return f"""
            [INST] <<SYS>>
            You are {self.name}: {self.desc}. 
            Keep your responses brief, 1-2 sentences.
            Only respond as {self.name}
            Here is the chat history
            {self.memory.previous()}
            <</SYS>>
            {self.memory.last()}
            [/INST]
            {self.name}:"""
    
    def initiative_template(self):
        return f"""
            [INST] <<SYS>>
            You are {self.name}: {self.desc}. 
            Should you respond at this point in the conversation?
            Answer with YES or NO in this format:
            Answer: YES
            Here is the chat history
            {self.memory.previous()}
            <</SYS>>
            {self.memory.last()}
            [/INST]
            Answer:"""