"""Core logic for tutr."""

import logging
import shutil

from tutr.config import TutrConfig
from tutr.context import gather_context, get_system_info
from tutr.llm import query_llm
from tutr.models import CommandResponse
from tutr.prompt import build_messages

log = logging.getLogger("tutr")
MAX_QUERY_LENGTH = 1000


def parse_input(words: list[str]) -> tuple[str | None, str]:
    """Split raw input words into an optional command and a query string.

    When the first word is an executable on ``PATH`` it is used as the command
    context; the remaining words become the query.  Otherwise the entire input
    is treated as the query with no command context.

    Args:
        words: Non-empty list of whitespace-split CLI tokens.

    Returns:
        A ``(cmd, query)`` tuple where *cmd* is the resolved executable name
        or ``None``, and *query* is the natural-language request string.
    """
    first, rest = words[0], words[1:]
    if shutil.which(first):
        cmd = first
        query = " ".join(rest) if rest else ""
    else:
        cmd = None
        query = " ".join(words)
    log.debug("cmd=%s query=%r", cmd, query)
    return cmd, query


def validate_query_length(query: str) -> None:
    """Raise when query exceeds the supported maximum length.

    Args:
        query: The user's natural-language query string.

    Raises:
        ValueError: If *query* is longer than ``MAX_QUERY_LENGTH`` characters.
    """
    query_len = len(query)
    if query_len > MAX_QUERY_LENGTH:
        raise ValueError(
            f"Query is too long ({query_len} characters). "
            f"Please keep queries under {MAX_QUERY_LENGTH} characters."
        )


def run_query(query: str, config: TutrConfig, cmd: str | None = None) -> CommandResponse:
    """Run the core tutr pipeline for a pre-parsed query string.

    Gathers shell context and system info, builds LLM messages, and returns
    the LLM response.

    Args:
        query: The natural-language query string.
        config: Tutr configuration used for the LLM call.
        cmd: Optional command name that provides additional shell context.

    Returns:
        Parsed command suggestion and explanation from the LLM.
    """
    context = gather_context(cmd)
    system_info = get_system_info()
    messages = build_messages(cmd, query, context, system_info)
    return query_llm(messages, config)


def run(words: list[str], config: TutrConfig) -> CommandResponse:
    """Run the core tutr pipeline: parse input, gather context, query LLM.

    Args:
        words: Non-empty list of whitespace-split CLI tokens from the user.
        config: Tutr configuration used for the LLM call.

    Returns:
        Parsed command suggestion and explanation from the LLM.

    Raises:
        ValueError: If the parsed query exceeds ``MAX_QUERY_LENGTH`` characters.
    """
    cmd, query = parse_input(words)
    validate_query_length(query)
    return run_query(query, config, cmd=cmd)
