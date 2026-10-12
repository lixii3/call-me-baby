from typing import Any, Dict
from typing_extensions import Self
from pydantic import BaseModel, Field, model_validator, ValidationError

class Funct(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    parameters: dict[str, str] = {}
    returns: str | None = None


class Output(BaseModel):
    prompt: str = Field(min_length=1)
    funct: Funct
    parameters: Dict[str, Any] = {}

    @model_validator(mode="after")
    def validator(self) -> Self:
        if len(self.parameters) != len(self.funct.parameters):
            raise ValidationError(f"unmatched number of parameters provided for function: '{self.funct.name}'")
        for name, value in self.parameters.items():
            if self.funct.parameters.get(name) is None:
                raise ValidationError(f"parameter '{name}' does not belong to function '{self.funct.name}'")
            if not check_type_by_string(value, self.funct.parameters.get(name)):
                raise ValidationError(f"unmatched pair parameter value/parameter type; got: {value}, expected type: {self.funct.parameters.get(name)}")
        return self


def check_type_by_string(value, type_name_str):
    # Resolve the string to the actual type object
    target_type = globals().get(type_name_str)
    
    if target_type is None:
        raise TypeError(f"Type '{type_name_str}' is not defined in the current global scope.")
        
    # Check if value is an instance of the resolved type
    return isinstance(value, target_type)