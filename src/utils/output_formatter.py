from .data_validators import Response
import json
from pathlib import Path


def add_responses_to_json(responses: list[Response], jsonfile_path: Path) -> None:
    data = [response.get_dict() for response in responses]
    with jsonfile_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)