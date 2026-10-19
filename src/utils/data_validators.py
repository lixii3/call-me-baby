from typing import Any, Dict
from typing_extensions import Self
from pydantic import BaseModel, Field, model_validator, ValidationError
from pathlib import Path


class Funct(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    parameters: dict[str, Any] = {}
    returns: str | None = None


class Response(BaseModel):
    prompt: str = Field(min_length=1)
    funct: Funct
    parameters: Dict[str, Any] = {}

    @model_validator(mode="after")
    def validator(self) -> Self:
        if len(self.parameters) != len(self.funct.parameters):
            raise ValueError("unmatched number of parameters provided "
                             f"for function: '{self.funct.name}'")
        for name, value in self.parameters.items():
            if self.funct.parameters.get(name) is None:
                raise ValueError(f"parameter '{name}' does not belong to "
                                 f"function '{self.funct.name}'")
            if not check_json_typing_by_str(value,self.funct.parameters.get(name, "")):
                raise ValueError(f"unmatched pair parameter value/parameter type; got: {value}, "
                                 f"expected type: {self.funct.parameters.get(name)}")
        return self

    def get_dict(self) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        ret["prompt"] = self.prompt
        ret["name"] = self.funct.name
        ret["parameters"] = self.parameters
        return ret


def check_json_typing_by_str(value: Any, type_name_str: str) -> bool:
    # Resolve the string to the actual type object
    type_name_str = type_name_str.lower()
    if type_name_str == 'number':
        return isinstance(value, int | float)
    if type_name_str == 'string':
        return isinstance(value, str)
    if type_name_str =="boolean":
        return isinstance(value, bool)
    if type_name_str =="array":
        return isinstance(value, list)
    if type_name_str =="object":
        return isinstance(value, dict)

    target_type = globals().get(type_name_str)
    if target_type is None:
        raise TypeError(f"Type '{type_name_str}' is not defined in "
                        "the current global scope.")
    # Check if value is an instance of the resolved type
    return isinstance(value, target_type)
