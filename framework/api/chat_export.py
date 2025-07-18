from framework.helpers import persist_chat
from framework.helpers.api import ApiHandler, Input, Output, Request


class ExportChat(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")

        context = self.get_context(ctxid)
        content = persist_chat.export_json_chat(context)
        return {
            "message": "Chats exported.",
            "ctxid": context.id,
            "content": content,
        }
