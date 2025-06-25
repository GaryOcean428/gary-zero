from framework.helpers.api import ApiHandler, Input, Output, Request


class Nudge(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")

        context = self.get_context(ctxid)
        context.nudge()

        msg = "Process reset, agent nudged."
        context.log.log(type="info", content=msg)

        return {
            "message": msg,
            "ctxid": context.id,
        }
