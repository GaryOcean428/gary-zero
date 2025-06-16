from python.helpers.api import ApiHandler, Input, Output, Request


class GetHistory(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", [])
        context = self.get_context(ctxid)
        agent = context.streaming_agent or context.agent0
        history = agent.history.output_text()
        size = agent.history.get_tokens()

        return {"history": history, "tokens": size}
