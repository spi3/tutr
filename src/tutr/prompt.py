"""Prompt construction for tutr."""

import json
from typing import TypedDict

from tutr.models import CommandResponse

SYSTEM_PROMPT = f"""\
You are a terminal command assistant. Your job is to generate the exact terminal \
command that accomplishes what the user describes.

<critical>
Return **ONLY** valid JSON matching this schema: 

{json.dumps(CommandResponse.model_json_schema())}

Hard requirements:
- Output exactly one JSON object and nothing else.
- The first character of your response must be `{{` and the last character must be `}}`.
- Do not include markdown, code fences, comments, prefixes, or suffixes.
- Do not include analysis, reasoning, or explanatory prose outside JSON fields.
- Never output tokens such as `start_thought`, `thoughtful`, `<think>`, or similar reasoning markers.
- Ensure the JSON is syntactically valid and parseable by `json.loads`.
- Use only keys defined by the schema above.

</critical>
"""


class LLMMessage(TypedDict):
    """Single chat message for the LLM API."""

    role: str
    content: str


def build_messages(
    cmd: str | None, query: str, context: str, system_info: str = ""
) -> list[LLMMessage]:
    """Build the message list for the LLM call."""
    parts: list[str] = []

    if system_info:
        parts.append(f"System:\n{system_info}")

    if cmd is not None:
        parts.append(f"Command: {cmd}")
        parts.append(f"Context:\n{context}")

    parts.append(f"What I want to do: {query}")

    user_content = "\n\n".join(parts)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
