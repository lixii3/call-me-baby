from src.parsing import parse_args, parse_prompts, parse_functions, ParsingException
from src.utils import Funct, Response, add_responses_to_json
import random as rm
import numpy as np
import json
from pathlib import Path
from pydantic import ValidationError
# try:
#     # from llm_sdk.llm_sdk import Small_LLM_Model
# except ImportError as e:
#     print(e)
#     exit()

def main() -> None:
    # parse input data from json files
    try:
        args: dict[str, Path] = parse_args()
        prompts: list[str] = parse_prompts(args.get("input", Path("")))
        functions: list[Funct] = parse_functions(args.get("functions_definition", Path("")))
        if not len(prompts) or not len(functions):
            raise ParsingException("empty input or functions_definitions file")
    except ParsingException as e:
        print(e)
        exit()
        
    # test Respose
    outs: List[Response] = []
    for prompt in prompts:
        f = rm.choice(functions)
        parameters: dict[str, Any] = {}
        for k, v in f.parameters.items():
            parameters[k] = "42"
        try:
            outs.append(Response(prompt=prompt, funct=f, parameters=parameters))
        except ValidationError as e:
            print(e)
    
    add_responses_to_json(outs, args["output"])
    


if __name__ == "__main__":
    main()