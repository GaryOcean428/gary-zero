from agent import AgentContext
from zero.api.message import Message
from zero.helpers.defer import DeferredTask


class MessageAsync(Message):
    async def respond(self, task: DeferredTask, context: AgentContext):
        return {
            "message": "Message received.",
            "context": context.id,
        }
