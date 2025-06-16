from python.helpers import runtime
from python.helpers.api import ApiHandler, Input, Output, Request


class RFC(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        result = await runtime.handle_rfc(input)  # type: ignore
        return result
