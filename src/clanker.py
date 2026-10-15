try:
    from llm_sdk.llm_sdk import Small_LLM_Model as Baby
    from src.utils import Response, Funct, Path
except ImportError as e:
    print(e)
    exit()

def test(args: dict[str, Path], functions: list[Funct], prompts: list[str]) -> None:
    baby: Baby = Baby()
    
    