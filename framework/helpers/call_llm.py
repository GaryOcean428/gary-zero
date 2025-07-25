from collections.abc import Callable
from typing import TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import BaseLLM
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)


class Example(TypedDict):
    input: str
    output: str


async def call_llm(
    system: str,
    model: BaseChatModel | BaseLLM,
    message: str,
    examples: list[Example] = None,
    callback: Callable[[str], None] | None = None,
):
    if examples is None:
        examples = []
    example_prompt = ChatPromptTemplate.from_messages(
        [
            HumanMessage(content="{input}"),
            AIMessage(content="{output}"),
        ]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=examples,  # type: ignore
        input_variables=[],
    )

    few_shot_prompt.format()

    final_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system),
            few_shot_prompt,
            HumanMessage(content=message),
        ]
    )

    chain = final_prompt | model

    response = ""
    async for chunk in chain.astream({}):
        # await self.handle_intervention()  # wait for intervention and handle it, if paused

        if isinstance(chunk, str):
            content = chunk
        elif hasattr(chunk, "content"):
            content = str(chunk.content)
        else:
            content = str(chunk)

        if callback:
            callback(content)

        response += content

    return response
