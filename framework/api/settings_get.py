from framework.helpers import settings
from framework.helpers.api import ApiHandler, Input, Output, Request


class GetSettings(ApiHandler):
    async def process(self, input_data: Input, request: Request) -> Output:
        try:
            current_settings = settings.get_settings()
            print(f"DEBUG: Current settings keys: {list(current_settings.keys())}")
            print(f"DEBUG: Settings has api_keys: {'api_keys' in current_settings}")

            settings_data = settings.convert_out(current_settings)
            print(f"DEBUG: Generated {len(settings_data['sections'])} sections")
            for section in settings_data['sections']:
                print(f"DEBUG: Section: {section['id']} - {section['title']}")

            return {"settings": settings_data}
        except Exception as e:
            print(f"ERROR in GetSettings: {e}")
            import traceback
            traceback.print_exc()
            raise
