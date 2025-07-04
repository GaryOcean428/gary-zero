from framework.helpers import settings
from framework.helpers.api import ApiHandler, Input, Output, Request


class SetSettings(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        settings_data = settings.convert_in(input_data)
        settings.set_settings(settings_data)
        return {"settings": settings_data}
