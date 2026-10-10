from src.parsing import parse_args, parse_prompts
try:
    from pathlib import Path
    from llm_sdk.llm_sdk import Small_LLM_Model
except ImportError as e:
    print(e)
    exit()


if __name__ == "__main__":
    args: dict[str, Path] = parse_args()
    prompts = parse_prompts(args["input"])
    bobby = Small_LLM_Model()
    # helpme