import dataclasses
import json
import logging
from typing import AsyncGenerator

from error.error import error_response


class JSONEncoder(json.JSONEncoder):
    """
    Encoder for the LLM response
    """

    def default(self, o):
        # Check if the object is a dataclass and not an instance of a dataclass
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        return super().default(o)

    @staticmethod
    async def format_as_ndjson(r: AsyncGenerator[dict, None], language: str) -> AsyncGenerator[str, None]:
        try:
            async for event in r:
                yield json.dumps(event, ensure_ascii=False, cls=JSONEncoder) + "\n"
        except Exception as error:
            logging.exception("Exception while generating response stream: %s", error)
            yield json.dumps(error_response(error, language))
