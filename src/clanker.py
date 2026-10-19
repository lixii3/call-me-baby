from llm_sdk import Small_LLM_Model as Baby
from utils import get_baby_best_token, Funct
from torch import Tensor
from scr.con


baby: Baby = Baby()


def answer_the_call_baby_please(prompt: str, functions: list[Funct]) -> None:
    '''Single prompt loop'''
    start_answer: str = "Agent Response: "
    mod_prompt: str = f"User Request: {prompt}\n" +\
       "function name -> [put name here], " +\
       "parameters values -> [value1, " +\
       "value2, ...]\nYou have to provide what is supposed to go in the square brakets, " +\
       "to do what the user asked you." +\
       f"{start_answer}"
    ids: list[Tensor] = baby.encode(mod_prompt)
    bestoken: int = get_baby_best_token(ids, baby)
    s = baby.decode(ids)
    s = s.split(start_answer)[-1]
    is_valid(ids, baby.decode(bestoken))


