"""LiteLLM client — thin async wrapper for model completions."""

import logging

import litellm

litellm.suppress_debug_info = True
logging.getLogger("LiteLLM").setLevel(logging.WARNING)


async def acompletion(
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    api_key: str | None = None,
    api_base: str | None = None,
) -> str:
    """Run an async litellm completion and return the text content."""
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if api_key is not None:
        kwargs["api_key"] = api_key
    if api_base is not None:
        kwargs["api_base"] = api_base

    response = await litellm.acompletion(**kwargs)
    return response.choices[0].message.content
