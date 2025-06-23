from zero.helpers import persist_chat
from zero.helpers.api import ApiHandler, Input, Output, Request


class Reset(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")

        # context instance - get or create
        context = self.get_context(ctxid)
        context.reset()
        persist_chat.save_tmp_chat(context)

        return {
            "message": "Agent restarted.",
        }
