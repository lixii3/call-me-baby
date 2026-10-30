*This project has been created as part of the 42 curriculum by lmongili.*

# Call Me Maybe

## Description

Call Me Maybe is a small language-model function-calling project. Given a user
prompt and a list of function schemas, it asks a local causal language model to
produce one function name and its arguments. Constrained decoding filters
candidate tokens as they are generated so the output follows the project's
function-call syntax, contains JSON argument values, and uses the declared
parameter types. The completed call is parsed and written to a JSON file; the
program does not execute the selected function.

The inference wrapper in the `llm_sdk` workspace package uses the
`Qwen/Qwen3-0.6B` model by default.

## Instructions

### Requirements and installation

- Python 3.10
- [uv](https://docs.astral.sh/uv/)
- Internet access on the first run to download the model and tokenizer from
  Hugging Face, unless they are already cached
- Enough memory for the model. Inference uses CUDA when available and otherwise
  falls back to CPU; CPU inference may be slow.

Install the project dependencies and the lint tools used by the Makefile:

```sh
make install
```

### Input files

Provide a function-definition JSON file containing an array of schemas. Each
schema has a `name`, optional `description`, `parameters` whose entries specify
a `type`, and a `returns` type. For example:

```json
[
  {
    "name": "fn_multiply_numbers",
    "description": "Multiply two numbers.",
    "parameters": {
      "a": { "type": "number" },
      "b": { "type": "number" }
    },
    "returns": { "type": "number" }
  }
]
```

The prompt input is JSON containing one or more objects with a string-valued
`prompt` field. Prompts are collected recursively from nested objects and
arrays:

```json
[
  { "prompt": "What is the product of 3 and 5?" }
]
```

### Run

Run the module with explicit paths for the required function definitions,
prompt input, and output:

```sh
uv run python -m src \
  --functions_definition path/to/functions.json \
  --input path/to/prompts.json \
  --output path/to/function_calls.json
```

The output is a JSON array containing each prompt, the chosen function name,
and its parameters. The program generates at most 3,000 tokens per call; it
reports an error if generation cannot continue with a valid prefix or does
not complete within that limit.

The Makefile also provides an end-to-end sample command:

```sh
make test
```

It expects `test/input/functions_definition.json` and
`test/input/prompt_test.json` to be available, and writes to
`test/output/test_output.json`. These test fixtures are not tracked in this
repository, so provide them or use your own input paths if they are absent.

To run with your own files through the Makefile:

```sh
make run ARGS="--functions_definition path/to/functions.json --input path/to/prompts.json --output path/to/function_calls.json"
```

## Algorithm explanation

The constrained decoding implementation is in `src/constrained_decoding.py`,
and token selection is performed in `src/clanker.py`.

1. The application builds a prompt that describes the available functions,
   parameter names and types, and the required one-line output format.
2. At each generation step, it obtains the model's next-token logits and
   examines candidate token IDs in descending logit order.
3. Each candidate is decoded together with the tokens already generated. The
   resulting text is checked as a *prefix*: a prefix may be incomplete but
   must still be extendable to a valid call for at least one declared function.
   Candidates that cannot form such a prefix are rejected, and the
   highest-ranked remaining candidate is selected.
4. Prefix validation matches the exact function name and parameter order,
   checks separators and the terminating semicolon, and incrementally parses
   JSON strings, numbers, booleans, `null`, arrays, and objects. It distinguishes
   invalid input from valid-but-incomplete input. Parameter values are checked
   against their declared primitive/container types. A parameter named
   `regex` is additionally checked for a compilable regular expression.
5. Generation ends when a valid complete call reaches the end-of-sequence
   token, or when the implementation detects a completed call. The final text
   is parsed again into a response and validated before it is written.

The accepted syntax is this project's function-call format, not a general
function-calling standard: the function name is followed by ordered
`parameter: JSON_VALUE` entries separated by commas and a semicolon. For
example:

```text
fn_multiply_numbers a: 3, b: 5;
```

## Design decisions

- **Constrain generation instead of repairing it afterward.** Filtering
  candidates at every step prevents invalid continuations from being chosen,
  rather than relying solely on retries or post-generation correction.
- **Validate decoded prefixes.** Token boundaries do not necessarily align with
  names, punctuation, or JSON values, so grammar checks operate on the decoded
  text accumulated so far.
- **Keep the schema as the source of truth.** Function names, parameter order,
  and expected types come from the supplied definitions; the output parser
  checks the same constraints before returning a response.
- **Emit structured data, not an executed action.** The result is a parsed
  function name and argument object stored in JSON. Calling the function is
  outside this program's scope.
- **Use a local Hugging Face model wrapper.** The bundled workspace SDK loads
  the model and tokenizer through Transformers and automatically selects an
  available accelerator or CPU.

## Performance analysis

No measured accuracy, latency, or throughput benchmark is included in this
repository, so no numerical performance claims are made.

- **Accuracy and validity:** Accepted output is checked against the implemented
  call syntax and declared parameter types, then parsed again before writing.
  This constrains format validity; it does not guarantee that the chosen
  function or values correctly answer the user's request.
- **Speed:** Each output token requires a model forward pass. The implementation
  ranks the vocabulary and tests decoded candidates, reparsing prefixes as
  needed. It does not use a generation KV cache in this loop, so long outputs,
  large vocabularies, and CPU inference can make generation slow. Constrained
  candidate checks add work on top of model inference.
- **Reliability:** Invalid next-token candidates are skipped, and EOS is only
  accepted for a complete call. If no candidate can continue a valid call, or
  the token limit is reached, the program raises a visible generation error
  instead of treating a partial call as successful. The final parse provides
  an additional validation step.

## Challenges faced

- **Partial tokens can split syntax.** A model token may contain only part of a
  function name, JSON escape, or delimiter. The prefix parser treats an
  extendable fragment as incomplete rather than rejecting it prematurely.
- **Nested and escaped JSON needs stateful validation.** Strings, escapes,
  arrays, and objects require distinguishing malformed input from a value
  whose remaining characters have not been generated. The parser advances
  through the available text and reports whether a value is invalid,
  incomplete, or complete.
- **The model may prefer a high-scoring invalid continuation.** Candidate
  tokens are tried in logit order, but only candidates that preserve at least
  one complete schema-compatible call are accepted.
- **A syntactically valid prefix is not yet a complete response.** Completion
  checks and a final parse/type validation prevent partial output from being
  returned as a successful function call.

## Testing strategy

The repository supplies an end-to-end Makefile target rather than a tracked
unit-test suite. `make test` runs the CLI against the sample function and
prompt JSON files and writes the generated response to the configured output
path. Because it uses the language model, it also depends on model availability
and may take time; its generated argument values are model-dependent.

The implementation's validation strategy checks incremental prefixes during
generation and validates the completed output again through `parse_output` and
the response model. For a manual run, inspect the output JSON and verify that
the selected function is declared, all required parameters are present in
order, and their values match the schema types.

## Example usage

With the sample schema and prompt files available, run:

```sh
uv run python -m src \
  --functions_definition test/input/functions_definition.json \
  --input test/input/prompt_test.json \
  --output test/output/test_output.json
```

For the prompt “What is the product of 3 and 5?”, a valid *format* of result
would look like this (the actual model response can vary):

```json
[
  {
    "prompt": "What is the product of 3 and 5?",
    "name": "fn_multiply_numbers",
    "parameters": {
      "a": 3.0,
      "b": 5.0
    }
  }
]
```

### Edge Cases

This project is strictly focused on training and guiding an LLM to respond to
your requests ONLY using the provided resources, which, in this case, are the
functions defined in the specified file.
Given that, any requests that do not match a specific given function will be
considered as an undefined behaviour case. All the machine can do is choosing
a function that it consideres the best match given my constraints, that is all.

In any case, though, this machine will always provide a valid JSON output with
an existent function even in cases where it doesn't match the request.
This is the best way I found to handle improper requests.

## Resources

- [RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259) — JSON syntax and data types.
- [Python `json` documentation](https://docs.python.org/3/library/json.html) — JSON parsing and serialization used by the project.
- [Python `re` documentation](https://docs.python.org/3/library/re.html) — regular-expression compilation used for the `regex` parameter check.
- [Pydantic documentation](https://docs.pydantic.dev/) — model validation used for function and response data.
- [Hugging Face Transformers documentation](https://huggingface.co/docs/transformers/) — model and tokenizer loading through the local SDK.
- [Qwen3-0.6B on Hugging Face](https://huggingface.co/Qwen/Qwen3-0.6B) — model used by default.
- [uv documentation](https://docs.astral.sh/uv/) — dependency and environment management.

**AI use:** AI assistance (Copilot) was used for this README task to inspect the
repository's implementation and draft its project, algorithm, usage, testing,
and performance descriptions. This statement describes assistance with this
documentation; it does not claim that AI generated or validated the project
implementation.
