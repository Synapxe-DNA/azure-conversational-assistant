import json
import dataclasses

class JSONEncoder(json.JSONEncoder):
    """
    Encoder for the LLM response
    """
    def default(self, o):
        # Check if the object is a dataclass and it is an instance of a dataclass and not a class
        if dataclasses.is_dataclass(o) and not isinstance(o, type): 
            return dataclasses.asdict(o)
        return super().default(o)