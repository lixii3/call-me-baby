from src.parsing import parse_args, parse_prompts, \
    parse_functions, ParsingException
from src.utils import Funct
from pathlib import Path
from src.clanker import call_me_baby, BabyCallException
import datetime


def main() -> None:
    # parse input data from json files
    start_time: datetime.datetime = datetime.datetime.now()
    try:
        args: dict[str, Path] = parse_args()
        prompts: list[str] = parse_prompts(args.get("input", Path("")))
        functions: list[Funct] = parse_functions(args.get(
            "functions_definition", Path("")))
        if not len(prompts) or not len(functions):
            raise ParsingException("empty input or functions_definitions file")
    except ParsingException as e:
        print(e)
        exit()
    try:
        call_me_baby(args, functions, prompts)
    except (BabyCallException) as e:
        print(e)
    end_time: datetime.datetime = datetime.datetime.now()

    delta: datetime.timedelta = end_time - start_time
    total_seconds = int(delta.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)

    print(f"{minutes:02d}:{seconds:02d}")


if __name__ == "__main__":
    main()
