from python.helpers.api import ApiHandler, Input, Output, Request


class Pause(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        # input data
        paused = input.get("paused", False)
        ctxid = input.get("context", "")

        # context instance - get or create
        context = self.get_context(ctxid)

        context.paused = paused

        return {
            "message": "Agent paused." if paused else "Agent unpaused.",
            "pause": paused,
        }
