from python.helpers import process
from python.helpers.api import ApiHandler, Input, Output, Request, Response


class Restart(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        process.reload()
        return Response(status=200)
