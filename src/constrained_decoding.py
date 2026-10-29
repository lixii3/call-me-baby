import json
import re
from enum import Enum, auto
from typing import Any
from pydantic import BaseModel
from src.utils import Response

from src.utils import Funct, matches_type


class _InvalidJsonPrefix(ValueError):
    pass


class _PrefixState(Enum):
    INVALID = auto()
    INCOMPLETE = auto()
    COMPLETE = auto()


class _JsonPrefixParser(BaseModel):
    text: str
    position: int = 0

    def parse_value(self, regex: bool = False) -> bool:
        """Parse one JSON value; return False when the text ends mid-value."""
        if self.position >= len(self.text):
            return False

        char = self.text[self.position]
        if char == '"':
            return self._parse_string(regex=regex)
        if char == "[":
            return self._parse_array()
        if char == "{":
            return self._parse_object()
        if char in "-0123456789":
            return self._parse_number()
        if char in "tfn":
            literal = {"t": "true", "f": "false", "n": "null"}[char]
            remaining = self.text[self.position:]
            shared_length = min(len(remaining), len(literal))
            if remaining[:shared_length] == literal[:shared_length]:
                if len(remaining) < len(literal):
                    self.position = len(self.text)
                    # valid but incomplete
                    return False
                self.position += len(literal)
                # matches
                return True
        raise _InvalidJsonPrefix("not a JSON value prefix")

    def parse_regex_value(self, regex_str: str | None = None) -> bool:
        """Parse a JSON string containing a valid regular expression."""
        if regex_str is None:
            value_start = self.position
            if not self._parse_string():
                return False
            regex_str = self.text[value_start:self.position]
        if len(regex_str) < 2:
            return False
        if regex_str[0] != '"':
            raise _InvalidJsonPrefix("a regex parameter must be a JSON string")

        try:
            pattern = json.loads(regex_str)
        except json.JSONDecodeError as error:
            raise _InvalidJsonPrefix("invalid JSON string") from error
        try:
            re.compile(pattern)
        except re.error as error:
            raise _InvalidJsonPrefix("invalid regular expression") from error
        return True

    def parse_regex_str(self, regex_str: str | None = None) -> bool:
        return self.parse_regex_value(regex_str)

    def _parse_string(self, regex: bool = False) -> bool:
        regex_str = "\""
        self.position += 1
        while self.position < len(self.text):
            char = self.text[self.position]
            regex_str += char
            if char == '"':
                if regex:
                    self.parse_regex_value(regex_str)
                self.position += 1
                return True
            # rifiuto i control characters unscaped
            if ord(char) < 0x20:
                raise _InvalidJsonPrefix("unescaped control character")
            if char == "\\":
                self.position += 1
                if self.position >= len(self.text):
                    return False
                escape = self.text[self.position]
                # controlla valida sequenza esadecimale
                if escape == "u":
                    end = self.position + 5
                    digits = self.text[self.position + 1:end]
                    if len(digits) < 4:
                        if all(c in "0123456789abcdefABCDEF" for c in digits):
                            self.position = len(self.text)
                            return False
                        raise _InvalidJsonPrefix("invalid unicode escape")
                    if any(c not in "0123456789abcdefABCDEF" for c in digits):
                        raise _InvalidJsonPrefix("invalid unicode escape")
                    self.position = end
                    continue
                # se non rientra nei validi escapes
                if escape not in '"\\/bfnrt':
                    raise _InvalidJsonPrefix("invalid string escape")
            self.position += 1
        return False

    def _parse_number(self) -> bool:
        MAX_DECIMAL_DIGITS = 5
        decimal_digits = 0
        # SEGNO
        if self.text[self.position] == "-":
            self.position += 1
            if self.position == len(self.text):
                return False
        # SALTA ZERO INIZIALI
        if self.text[self.position] == "0":
            self.position += 1
        elif self.text[self.position] in "123456789":
            #CONTINUA FINCHE CI SONO DIGITS
            while self.position < len(self.text) and self.text[self.position].isdigit():
                self.position += 1
        else:
            raise _InvalidJsonPrefix("invalid number")

        # CONTROLLO LA PARTE FRAZIONARIA
        if self.position < len(self.text) and self.text[self.position] == ".":
            self.position += 1
            if self.position == len(self.text):
                return False
            if not self.text[self.position].isdigit():
                raise _InvalidJsonPrefix("invalid fraction")
            while self.position < len(self.text) and self.text[self.position].isdigit() and decimal_digits < MAX_DECIMAL_DIGITS:
                self.position += 1
                decimal_digits += 1

        # controllo esponente
        if self.position < len(self.text) and self.text[self.position] in "eE" and decimal_digits < MAX_DECIMAL_DIGITS:
            self.position += 1
            if self.position == len(self.text):
                return False
            if self.text[self.position] in "+-":
                self.position += 1
                if self.position == len(self.text):
                    return False
            if not self.text[self.position].isdigit():
                raise _InvalidJsonPrefix("invalid exponent")
            while self.position < len(self.text) and self.text[self.position].isdigit():
                self.position += 1
        return True

    def _skip_whitespace(self) -> None:
        while self.position < len(self.text) and self.text[self.position] in " \t\r\n":
            self.position += 1

    def _parse_array(self) -> bool:
        self.position += 1
        self._skip_whitespace()
        if self.position == len(self.text):
            return False
        # array vuoto ma valido
        if self.text[self.position] == "]":
            self.position += 1
            return True
        while True:
            #value incompleto
            if not self.parse_value():
                return False
            self._skip_whitespace()
            if self.position == len(self.text):
                return False
            char = self.text[self.position]
            if char == "]":
                self.position += 1
                return True
            if char != ",":
                raise _InvalidJsonPrefix("expected ',' or ']'")
            self.position += 1
            self._skip_whitespace()

    def _parse_object(self) -> bool:
        self.position += 1
        self._skip_whitespace()
        if self.position == len(self.text):
            return False
        # empty valid object
        if self.text[self.position] == "}":
            self.position += 1
            return True
        while True:
            if self.position == len(self.text):
                return False
            if self.text[self.position] != '"' or not self._parse_string():
                if self.position == len(self.text):
                    return False
                raise _InvalidJsonPrefix("expected an object key")
            self._skip_whitespace()
            if self.position == len(self.text):
                return False
            if self.text[self.position] != ":":
                raise _InvalidJsonPrefix("expected ':'")
            self.position += 1
            self._skip_whitespace()
            if not self.parse_value():
                return False
            self._skip_whitespace()
            if self.position == len(self.text):
                return False
            char = self.text[self.position]
            if char == "}":
                self.position += 1
                return True
            if char != ",":
                raise _InvalidJsonPrefix("expected ',' or '}'")
            self.position += 1
            self._skip_whitespace()


def _type_prefix_is_possible(value_prefix: str, type_name: str) -> bool:
    if not value_prefix:
        return True
    first: str = value_prefix[0]
    normalized: str = type_name.lower()
    if normalized == "integer":
        return re.fullmatch(r"-?(?:0|[1-9][0-9]*)?", value_prefix) is not None
    if normalized in {"number", "float"}:
        return first in "-0123456789"
    if normalized == "string":
        return first == '"'
    if normalized == "boolean":
        return first in "tf"
    if normalized == "array":
        return first == "["
    if normalized == "object":
        return first == "{"
    return False


def _function_prefix_state(text: str, function: Funct) -> _PrefixState:
    # se ancora deve essere generato il nome intero della fn
    if len(text) < len(function.name):
        if function.name.startswith(text):
            return _PrefixState.INCOMPLETE
        return _PrefixState.INVALID
    if not text.startswith(function.name):
        return _PrefixState.INVALID

    position = len(function.name)
    if not function.parameters:
        remaining = text[position:]
        if not remaining:
            return _PrefixState.INCOMPLETE
        if remaining == ";":
            return _PrefixState.COMPLETE
        return _PrefixState.INVALID

    parameters = list(function.parameters.items())
    for index, (parameter_name, parameter_type) in enumerate(parameters):
        literal = f"{parameter_name}: " if index > 0 else f" {parameter_name}: "
        remaining = text[position:]

        # controllo se deveessere ancora specificato il noe del parametro
        if len(remaining) < len(literal):
            if literal.startswith(remaining):
                return _PrefixState.INCOMPLETE
            return _PrefixState.INVALID
        if not remaining.startswith(literal):
            return _PrefixState.INVALID

        # controllo sul valore del parametro
        position += len(literal)
        parser = _JsonPrefixParser(text=text, position=position)
        try:
            if parameter_name == "regex":
                value_complete = parser.parse_regex_value()
            else:
                value_complete = parser.parse_value()
        except _InvalidJsonPrefix:
            return _PrefixState.INVALID
        value_prefix = text[position:parser.position]
        if not _type_prefix_is_possible(value_prefix, parameter_type):
            return _PrefixState.INVALID
        if not value_complete:
            return _PrefixState.INCOMPLETE

        try:
            value = json.loads(text[position:parser.position])
        except json.JSONDecodeError:
            return _PrefixState.INVALID
        if not matches_type(value, parameter_type):
            return _PrefixState.INVALID

        position = parser.position
        if index < len(parameters) - 1:
            while position < len(text) and text[position].isspace():
                position += 1
            if position >= len(text):
                return _PrefixState.INCOMPLETE
            if text[position] != ",":
                return _PrefixState.INVALID
            position += 1
            while position < len(text) and text[position].isspace():
                position += 1
        else:
            while position < len(text) and text[position].isspace():
                position += 1
            remaining = text[position:]
            if not remaining:
                return _PrefixState.INCOMPLETE
            if remaining != ";":
                return _PrefixState.INVALID
            position += 1

    if position == len(text):
        return _PrefixState.COMPLETE
    return _PrefixState.INVALID


def is_valid_output_prefix(partial: str, functions: list[Funct]) -> bool:
    """Return whether partial can still become a valid function call."""
    return any(
        _function_prefix_state(partial, function) is not _PrefixState.INVALID
        for function in functions
    )


def is_complete_output(text: str, functions: list[Funct]) -> bool:
    return any(
        _function_prefix_state(text, function) is _PrefixState.COMPLETE
        for function in functions
    )


def is_valid_token(partial: str, candidate: str, functions: list[Funct]) -> bool:
    """Compatibility helper for validating a decoded candidate token."""
    return is_valid_output_prefix(partial + candidate, functions)


def is_fn_name(candidate: str, functions: list[Funct]) -> bool:
    return any(candidate == function.name for function in functions)


def parse_output(text: str, functions: list[Funct], prompt: str) -> Response:
    """Parse a completed constrained-decoding result into its function and arguments."""
    for function in functions:
        parse_text = text
        if _function_prefix_state(parse_text, function) is not _PrefixState.COMPLETE:
            parse_text = text.rstrip()
            if _function_prefix_state(parse_text + ";", function) is not _PrefixState.COMPLETE:
                continue
        parameters: dict[str, Any] = {}
        position = len(function.name)
        parameter_names = list(function.parameters)
        for index, parameter_name in enumerate(parameter_names):
            literal = f"{parameter_name}: " if index > 0 else f" {parameter_name}: "
            position += len(literal)
            parser = _JsonPrefixParser(text=parse_text, position=position)
            if parameter_name == "regex":
                if not parser.parse_regex_value():
                    raise ValueError("incomplete JSON value in generated function call")
            else:
                if not parser.parse_value():
                    raise ValueError("incomplete JSON value in generated function call")
            parameters[parameter_name] = json.loads(parse_text[position:parser.position])
            position = parser.position
            if index < len(parameter_names) - 1:
                while position < len(parse_text) and parse_text[position].isspace():
                    position += 1
                if position >= len(parse_text) or parse_text[position] != ",":
                    raise ValueError("missing comma between function parameters")
                position += 1
                while position < len(parse_text) and parse_text[position].isspace():
                    position += 1
            else:
                while position < len(parse_text) and parse_text[position].isspace():
                    position += 1
                if position < len(parse_text):
                    if parse_text[position] != ";":
                        raise ValueError("missing function-call terminator")
                    position += 1
                if position != len(parse_text):
                    raise ValueError("unexpected content after function call")
        return Response(prompt=prompt, funct=function, parameters=parameters)
    raise ValueError(f"generated output is not a complete valid function call: {text!r}")
