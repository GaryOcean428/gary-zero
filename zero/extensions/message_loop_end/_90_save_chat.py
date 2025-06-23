from agent import LoopData
from zero.helpers import persist_chat
from zero.helpers.extension import Extension


class SaveChat(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        persist_chat.save_tmp_chat(self.agent.context)
