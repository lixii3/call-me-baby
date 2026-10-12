from src.parsing import parse_args, parse_prompts
from src.utils import Funct, Output
import numpy as np
import json
from pathlib import Path
from pydantic import ValidationError
# try:
#     # from llm_sdk.llm_sdk import Small_LLM_Model
# except ImportError as e:
#     print(e)
#     exit()


if __name__ == "__main__":
    args: dict[str, Path] = parse_args()
    # prompts = parse_prompts(args["input"])
    # bobby = Small_LLM_Model()
    # tensor = bobby.encode(prompts[0])
    try:
        with args["functions_definition"].open("r", encoding="utf-8") as json_file:
                    data = json.load(json_file)
    except (KeyError, OSError) as e:
        print(e)
        exit()
    functions: list[Funct] = []
    out: Output
    for d in data:
        dd = dict(d)
        name = str(dd["name"])
        description = str(dd["description"])
        parameters = {str(k): str(dict(v).get("type")) for k, v in dict(dd["parameters"]).items()}
        returns = str(dict(dd["returns"])["type"])
        try:
            f = Funct(name=name, description=description,
                      parameters=parameters, returns=returns)
        except (ValidationError, KeyError) as e:
            print(e)
            continue
        functions.append(f)
        print(str(f))
