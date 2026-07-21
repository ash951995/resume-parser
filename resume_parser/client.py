import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
_DEFAULT_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")


def call_claude(messages, system="", model=None, max_tokens=1000, tools=None, tool_choice=None):
    """
    Shared wrapper, same pattern as hello.py from Week 1 - defaults to
    Haiku for cost efficiency, override with model="claude-sonnet-5"
    for a quality check.
    """
    kwargs = {
        "model": model or _DEFAULT_MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools
    if tool_choice:
        kwargs["tool_choice"] = tool_choice

    return _client.messages.create(**kwargs)
