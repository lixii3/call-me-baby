from typing import Any, Dict
from typing_extensions import Self
from pydantic import BaseModel, Field, model_validator, ValidationError
from pathlib import Path
from .token_utills import matches_type


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
            type_p: str = self.funct.parameters.get(name, "")
            if self.funct.parameters.get(name) is None:
                raise ValueError(f"parameter '{name}' does not belong to "
                                 f"function '{self.funct.name}'")
            if not matches_type(value, type_p):
                raise ValueError(f"unmatched pair parameter value/parameter type; got: {value}, "
                                 f"expected type: {self.funct.parameters.get(name)}")
            if type_p.lower() == "number":
                self.parameters[name] = float(self.parameters[name])
        return self

    def get_dict(self) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        ret["prompt"] = self.prompt
        ret["name"] = self.funct.name
        ret["parameters"] = self.parameters
        return ret


