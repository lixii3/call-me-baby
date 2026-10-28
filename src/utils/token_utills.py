from llm_sdk import Small_LLM_Model as Baby
import numpy as np
import json
from torch import Tensor
from typing import Any


def get_token_list(baby: Baby) -> list[int]:
    tokens: list[int] = []
    data_dict: dict[str, int] = {}
    try:
        with open(baby.get_path_to_vocab_file(), 'r') as vocab:
            data_dict = json.load(vocab)
    except (OSError, json.JSONDecodeError) as e:
        raise e
    tokens = [v for k, v in dict(data_dict).items()]
    return tokens


def get_token_vocabulary(baby: Baby) -> dict[str, int]:
    data_dict: dict[str, int] = {}
    try:
        with open(baby.get_path_to_vocab_file(), 'r') as vocab:
            data_dict = json.load(vocab)
    except (OSError, json.JSONDecodeError) as e:
        raise e
    return dict(data_dict)


def get_baby_best_token(input_ids: Tensor | list[int], baby: Baby) -> int:
    if isinstance(input_ids, Tensor):
        input_ids = input_ids.reshape(-1).tolist()
    logits: list[float] = baby.get_logits_from_input_ids(input_ids)
    return int(np.argmax(logits))


def matches_type(value: Any, type_name: str) -> bool:
    normalized: str = type_name.lower()
    if normalized == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if normalized == "string":
        return isinstance(value, str)
    if normalized == "boolean":
        return isinstance(value, bool)
    if normalized == "array":
        return isinstance(value, list)
    if normalized == "object":
        return isinstance(value, dict)
    return False