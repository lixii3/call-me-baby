try:
    import sys
    import argparse
    from typing import List, Any
    import json
    from src.utils import Funct, Path, file_esistente
    from pydantic import ValidationError
except ImportError as e:
    print(e)
    exit()


class ParsingException(Exception):
    """Exception raised for an invalid parsing."""

    def __init__(self, msg: str = "") -> None:
        """Initialize a parsing error"""
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self) -> str:
        """Return the formatted parsing error."""
        return "Parsing Exception: " + self.msg


def perror(msg: str) -> None:
    print(msg, file=sys.stderr)


def parse_args() -> dict[str, Path]:
    argsdict: dict[str, Path]
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--functions_definition", required=True,
                            type=file_esistente,
                            default="data/input/functions_definition.json")
        parser.add_argument("--input",
                            type=file_esistente,
                            default="data/input/function_calling_tests.json")
        parser.add_argument("--output", type=Path,
                            default="data/output/function_calls.json")
    except argparse.ArgumentTypeError as e:
        raise ParsingException(str(e))
    argsdict = vars(parser.parse_args())
    # creo file di output se non esiste gia
    try:
        with argsdict["output"].open("r") as _:
            pass
    except OSError:
        argsdict["output"].parent.mkdir(parents=True, exist_ok=True)
    return argsdict


def parse_prompts(file: Path) -> List[str]:
    prompts: List[str] = []
    data: Any
    if file_esistente((str(file))):
        try:
            with file.open("r", encoding="utf-8") as json_file:
                data = json.load(json_file)

            def collect_prompts(value: object) -> None:
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key == "prompt" and isinstance(item, str):
                            prompts.append(item)
                        collect_prompts(item)
                elif isinstance(value, list):
                    for item in value:
                        collect_prompts(item)
        except (OSError, json.JSONDecodeError):
            raise ParsingException(f"error parsing file '{str(file)}'")
        collect_prompts(data)
        return prompts
    return []


def parse_functions(funct_def_file: Path) -> list[Funct]:
    functions: list[Funct] = []
    try:
        with funct_def_file.open("r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except (KeyError, OSError, json.JSONDecodeError):
        raise ParsingException(f"error parsing file '{str(funct_def_file)}'")
    for d in data:
        dd = dict(d)
        name = str(dd["name"])
        description = str(dd["description"])
        parameters = {str(k): str(dict(v).get("type"))
                      for k, v in dict(dd["parameters"]).items()}
        returns = str(dict(dd["returns"])["type"])
        try:
            f = Funct(name=name, description=description,
                      parameters=parameters, returns=returns)
        except (ValidationError) as e:
            raise ParsingException(msg=e.errors()[0]["msg"])
        except KeyError as e:
            raise ParsingException(f"{str(e)}")
        functions.append(f)
    return functions
