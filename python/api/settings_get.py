from python.helpers import settings
from python.helpers.api import ApiHandler, Input, Output, Request


class GetSettings(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        set = settings.convert_out(settings.get_settings())
        return {"settings": set}
