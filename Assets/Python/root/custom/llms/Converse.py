from custom.llms.custompipeline import TruePipeline
from datastructs.datalist import Entry
import re

class Converse(TruePipeline):
    def name(cls): return "CONVERSE"
    def max_tokens(cls):
        return 70
    def system_prompt(cls):
        return '''
            Assistant is a expert person creator and is able to determine who the user wishes to talk to and can describe them perfectly.
            Assistant will return the person that is to be generated, a short description of them, and their physical appearance.
            Format is Person: [person to create], Description: [who they are], Appearance: [What they look like].
            If assistant does not know who the person is, they can leave description and appearance as null.
            All of Assistant's communication is performed using this format.

            Here are some examples of conversations between user and Assistant:

            User: I am talking to batman
            Person: Batman, Description: batman is a bat-themed superhero who defends gotham city from criminals, Appearance: black and grey costume with a cape and glowing eyes.

            User: Hey its bob ross!
            Person: Bob ross, Description: a famous art teacher, Appearance: brown afro, blue shirt, smiling

            User: John Doe
            Person: John Doe, Description: null, Appearance: null

            From now on you should only respond using the format.
        '''

    def get_specifics(cls, result: str):
        m = re.match(r"^(?:.*\n)*?.*?Person: (.+?)[,\n ]*Description: (.+?)[,\n ]*Appearance: (.+?)(?:\n.*)*$", result)
        if m: return (m.group(1), m.group(2), m.group(3))
        else: return result

    def service(cls) -> str:
        return "NPCLLMs"
    
    def spoken(cls, result) -> str:
        person, desc, appearance = result
        return f"Spawning {person}."
    
    def to_entries(cls, result) -> list[Entry]:
        person, desc, appearance = result
        return [Entry("npc.create-name", person), Entry("npc.create-desc", desc), Entry("npc.create-appearance", appearance)]