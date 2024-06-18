from custom.llms.custompipeline import TruePipeline
import re

class Answerer(TruePipeline):
    def name(cls): return "QUESTION"
    def max_tokens(cls):
        return 40
    def system_prompt(cls):
        return '''
            Assistant is a expert trivia master and is able to answer any question that the user has.
            Assistant will return the answer to the users question.
            Format is Answer: [answer]
            All of Assistant's communication is performed using this format.

            Here are some examples of conversations between user and Assistant:

            User: When were the pyramids made?
            Answer: Around 3200 BC

            User: How is plastic made?
            Answer: Plastics are made from natural materials such as cellulose, coal, natural gas, salt and crude oil through a polymerisation or polycondensation process.

            User: Why do we need to sleep?
            Answer: Sleep keeps us healthy and functioning well. It lets your body and brain repair, restore, and reenergize.

            From now on you should only respond using the format.
        '''

    def get_specifics(cls, result: str):
        m = re.match(r"^(?:.*\n)*?.*?Answer: (.+?)(?:\n.*)*$", result)
        if m: return (m.group(1),)
        else: return result

    def service(cls) -> str:
        return None
    
    def spoken(cls, result) -> str:
        return result[0]