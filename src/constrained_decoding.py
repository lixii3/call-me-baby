from .utils import Funct


def is_valid_token(partial: str, candidate: str, functions: list[Funct]) -> bool:
    if len(partial.split()) <= 0:
        if not is_fn_name(candidate, functions):
            return False
    return True


def is_fn_name(candidate: str, functions: list[Funct]) -> bool:
    for fn in functions:
        pass
    return True
