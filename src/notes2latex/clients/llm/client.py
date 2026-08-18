"""LiteLLM client — async chat completions."""

import logging

import litellm
from litellm.types.completion import ChatCompletionMessageParam

litellm.suppress_debug_info = True
logging.getLogger("LiteLLM").setLevel(logging.WARNING)


async def complete_text(
    model: str,
    messages: list[ChatCompletionMessageParam],
    temperature: float,
    max_tokens: int,
    api_key: str | None = None,
) -> str:
    """Run a completion and return the assistant's text.

    Raises ValueError if the model returns no content.
    """
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
    )
    content = response.choices[0].message.content
    if not content:
        msg = f"{model} returned an empty response"
        raise ValueError(msg)
    return content
