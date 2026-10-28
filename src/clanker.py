from llm_sdk import Small_LLM_Model as Baby

from src.constrained_decoding import (
    is_complete_output,
    is_valid_output_prefix,
    parse_output,
)
from src.utils import Funct, Path, Response, add_responses_to_json


baby: Baby = Baby()


def call_me_baby(args: dict[str, Path], functions: list[Funct], prompts: list[str]) -> None:
    responses: list[Response] = []
    for prompt in prompts:
        responses.append(answer_the_call_baby_please(prompt, functions))
    add_responses_to_json(responses, args["output"])


def answer_the_call_baby_please(prompt: str, functions: list[Funct]) -> Response:
    """Generate one function call, accepting only tokens that preserve its grammar."""
    function_schemas = "\n".join(
        f"- {function.name}: {function.description}; parameters: "
        + ", ".join(
            f"{name} ({type_name})" for name, type_name in function.parameters.items()
        )
        for function in functions
    )
    mod_prompt = (
        f"User request: {prompt}\n"
        f"Available functions:\n{function_schemas}\n"
        "Return only one function call on one line. Use the exact function name, "
        "then every parameter in the listed order as `name: JSON_VALUE`, separated "
        "by one space. JSON_VALUE must be valid JSON of the declared type; quote "
        "strings with JSON double quotes. Do not add an explanation.\n"
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
            # seleziono il token oppure lo scarto
            if is_valid_output_prefix(candidate, functions):
                print(candidate)
                selected_token = token_id
                generated_ids.append(token_id)
                input_ids.append(token_id)
                break

        if selected_token is None:
            raise RuntimeError(
                "The model has no token that can continue a valid function call."
            )
        if selected_token == eos_token_id:
            break
    else:
        raise RuntimeError(
            f"The model did not finish a valid function call within "
            f"{max_new_tokens} tokens. Generated prefix: {baby.decode(generated_ids)!r}"
        )

    output = baby.decode(generated_ids)
    function, parameters = parse_output(output, functions)
    return Response(prompt=prompt, funct=function, parameters=parameters)
