from framework.helpers.memory import Memory
from framework.helpers.tool import Response, Tool
from framework.tools.memory_load import DEFAULT_THRESHOLD


class MemoryForget(Tool):
    async def execute(self, query="", threshold=DEFAULT_THRESHOLD, filter="", **kwargs):
        db = await Memory.get(self.agent)
        dels = await db.delete_documents_by_query(
            query=query, threshold=threshold, filter=filter
        )

        result = self.agent.read_prompt(
            "fw.memories_deleted.md", memory_count=len(dels)
        )
        return Response(message=result, break_loop=False)
