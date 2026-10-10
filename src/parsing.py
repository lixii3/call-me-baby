try:
    import sys
    import argparse
    from typing import List
    from .utils import file_esistente
    from pathlib import Path
    import json
except ImportError as e:
    print(e)
    exit()


def perror(msg: str) -> None:
    print(msg, file=sys.stderr)


def parse_args() -> dict[str, Path]:
    argsdict: dict[str, Path]
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--functions_definition", required=True,
                            type=file_esistente, default="data/input/functions_definition.json")
        parser.add_argument("--input", default="data/input/function_calling_tests.json", type=file_esistente)
        parser.add_argument("--output", default="data/output/function_calls.json", type=Path)
    except argparse.ArgumentTypeError as e:
        print(e)
        exit()
    argsdict = vars(parser.parse_args())
    return argsdict

def parse_prompts(file: Path) -> List[str]:
    if file_esistente(file):
        try:
            with file.open("r", encoding="utf-8") as json_file:
                data = json.load(json_file)

            prompts: List[str] = []

            def collect_prompts(value: object) -> None:
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key == "prompt" and isinstance(item, str):
                            prompts.append(item)
                        collect_prompts(item)
                elif isinstance(value, list):
                    for item in value:
                        collect_prompts(item)
        except OSError as e:
            print(e)
            exit()
        collect_prompts(data)
        print(prompts)
        return prompts
    return []
        