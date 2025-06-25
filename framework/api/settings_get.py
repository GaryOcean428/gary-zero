from framework.helpers import settings
from framework.helpers.api import ApiHandler, Input, Output, Request


class GetSettings(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        settings_data = settings.convert_out(settings.get_settings())
        return {"settings": settings_data}
