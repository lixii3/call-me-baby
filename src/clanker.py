from llm_sdk import Small_LLM_Model as Baby

from src.constrained_decoding import (
    is_complete_output,
    is_valid_output_prefix,
    parse_output,
)
from src.utils import Funct, Path, Response, add_responses_to_json


class BabyCallException(Exception):
    def __init__(self,
                 msg: str = "exception occured while calling baby :(") -> None:
        super().__init__(msg)
        self.msg = msg

    def __str__(self) -> str:
        return "BabyCallException: " + self.msg


baby: Baby = Baby()


def call_me_baby(args: dict[str, Path], functions: list[Funct],
                 prompts: list[str]) -> None:
    responses: list[Response] = []
    for prompt in prompts:
        responses.append(answer_the_call_baby_please(prompt, functions))
    try:
        add_responses_to_json(responses, args["output"])
    except (OSError, TypeError):
        raise BabyCallException("error while dumping to json output file")


def answer_the_call_baby_please(prompt: str,
                                functions: list[Funct]) -> Response:
    """Generate one function call, accepting only tokens
    that preserve its grammar."""
    if prompt == "":
        prompt = " "
    function_schemas = "\n".join(
        f"- {function.name}: {function.description}; parameters: "
        + ", ".join(
            f"{name} ({type_name})"
            for name, type_name in function.parameters.items()
        )
        for function in functions
    )
    mod_prompt = (
        f"User request: {prompt}\n"
        f"Available functions:\n{function_schemas}\n"
        "Return only one function call on one line. Use the exact "
        "function name, then every parameter in the listed order as `name: "
        "JSON_VALUE`, separated by commas. "
        "Terminate the call with a semicolon."
        " JSON_VALUE must be valid JSON of the declared type; quote strings "
        "with JSON double quotes. "
        "Do not add an explanation.\n"
        "Function call: "
    )
    input_ids: list[int] = baby.encode(mod_prompt).squeeze(0).tolist()
    generated_ids: list[int] = []
    max_new_tokens = 3000
    eos_token_id = baby.get_eos_token_id()
    for _ in range(max_new_tokens):
        logits = baby.get_logits_from_input_ids(input_ids)
        ranked_token_ids = sorted(
            range(len(logits)), key=logits.__getitem__, reverse=True
        )
        partial = baby.decode(generated_ids)
        selected_token: int | None = None

        for token_id in ranked_token_ids:
            if token_id == eos_token_id:
                if is_complete_output(partial, functions):
                    selected_token = token_id
                    break
                continue

            candidate_ids = generated_ids + [token_id]
            candidate = baby.decode(candidate_ids)
            if candidate == partial:
                continue
            if is_valid_output_prefix(candidate, functions):
                selected_token = token_id
                generated_ids.append(token_id)
                input_ids.append(token_id)
                break

        if selected_token is None:
            raise BabyCallException(
                "The model has no token that can continue a valid "
                f"function call. Generated prefix: {partial!r}"
            )
        if selected_token == eos_token_id:
            break
        # CONTROLLA SE LA FUNCTION CALL E' GIA' COMPLETA, IN TAL
        # CASO NON CONTINUO A CERCARE TOKEN
        if baby.decode([selected_token]).isspace():
            try:
                parse_output(candidate, functions, prompt)
                break
            except ValueError:
                continue
    else:
        raise BabyCallException(
            f"The model did not finish a valid function call within "
            f"{max_new_tokens} tokens. "
            f"Generated prefix: {baby.decode(generated_ids)!r}"
        )

    output: str = baby.decode(generated_ids)
    response: Response = parse_output(output, functions, prompt)
    print(str(response))
    return response
