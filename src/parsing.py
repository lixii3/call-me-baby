from llm_sdk.llm_sdk import Small_LLM_Model as bob
import sys
import argparse
from typing import List
from pydantic import BaseModel

flags: List[str] = ["--functions_definition", " --input", "--output"]

def perror(msg: str) -> None:
    print(msg, file=sys.stderr)

def parsing() -> bob:
    parser = argparse.ArgumentParser()
    parser.add_argument("--functions_definition", required=True)
    parser.add_argument("--output", default="data/output")
    parser.add_argument("--input", default="data/input")
    
    args = parser.parse_args()
    print(args)
    return bob()

