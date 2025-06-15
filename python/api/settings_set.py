from python.helpers import settings
from python.helpers.api import ApiHandler, Input, Output, Request


class SetSettings(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        set = settings.convert_in(input)
        settings.set_settings(set)
        return {"settings": set}
