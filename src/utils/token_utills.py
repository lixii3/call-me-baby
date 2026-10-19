from llm_sdk import Small_LLM_Model as Baby
import numpy as np
import json


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


def get_baby_best_token(input_ids: list[Tensor], baby: Baby) -> int:
    logits: list[float] = baby.get_logits_from_input_ids(ids)
    best_idx: int = int(np.argmax(logits))
    best_token: int = get_token_list(baby)[best_idx]
    return best_token
