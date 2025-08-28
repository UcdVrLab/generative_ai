from custom.llms.custompipeline import TruePipeline
import re

class Controller(TruePipeline):
    def name(cls): return "CONTROLLER"
    def max_tokens(cls):
        return 10
    def system_prompt(cls):
        return '''
            Assistant is a expert user interpreter and can determine what the user wishes to happen from a prompt.
            Assistant will return one word, being the command that should be executed.
            All of Assistant's communication is performed using this format.

            Commands available to Assistant are:
            - "Converse": When the user wishes to talk to you or someone else.
            - "Question": When the user wishes to ask you a question.
            - "ObjGen": When the user wishes create an object.
            - "SkyGen": When the user wishes to create a skybox of a location.
            - "MultObjGen": When the user wants to create/complete a setup/collection/array of objects. (Hint keywords: 'array', 'setup', 'complete', 'several items') - The user may also list several items then "MultObjGen"
            - "Terminate": When the user wishes to stop the interaction.
            - "Confused": When you cannot figure out what the user wants or if the format is wrong.

            Here are some examples of conversations between user and Assistant:

            User: Hey how are you today?
            Command: Question

            User: When were the pyramids made?
            Command: Question

            User: I am holding a sword
            Command: ObjGen

            User: Create a large medieval axe
            Command: ObjGen

            User: I am in a cave
            Command: SkyGen

            User: Complete a primary school table setup with several items
            Command: MultObjGen

            User: Complete a full laboratory workspace with a microscope, bunsen burner and lab table
            Command: MultObjGen

            User: I am having a conversation with Darth Vader
            Command: Converse

            User: Complete a bedroom setup
            Command: MultObjGen

            User: I would like to stop
            Command: Terminate

            User: Create a table
            Command: ObjGen

            User: blah blah blah gibberish
            Command: Confused

            From now on you should only respond using the format.
        '''
    
    def get_specifics(cls, result: str):
        m = re.match(r"^(?:.*\n)*?.*?Command: (.+?)(?:\n.*)*$", result)
        if m: return (m.group(1).strip().upper(),)
        else: return result

    def service(cls) -> str:
        return None
    
    def spoken(cls, result) -> str:
        return result[0]
    