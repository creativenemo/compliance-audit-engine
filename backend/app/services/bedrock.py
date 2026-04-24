"""
Amazon Bedrock client wrapper — Amazon Nova model invocation.

Usage
-----
    from app.services.bedrock import invoke_nova, parse_json_response

    text = await invoke_nova(system_prompt="...", user_message="...")
    data = parse_json_response(text)
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from functools import lru_cache
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_bedrock_client() -> Any:
    """Return a cached boto3 bedrock-runtime client.

    The cache is process-scoped (one client per worker).  The client is
    thread-safe for concurrent invoke_model calls, so running it from an
    executor is safe.
    """
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.bedrock_region,
    )


# ---------------------------------------------------------------------------
# Public async entry-point
# ---------------------------------------------------------------------------

async def invoke_nova(
    system_prompt: str,
    user_message: str,
    model_id: str | None = None,
    max_tokens: int = 8192,
    temperature: float = 0.1,
) -> str:
    """Invoke an Amazon Nova model and return the assistant's reply text.

    boto3 is synchronous; this coroutine offloads the blocking call to the
    default thread-pool executor so the event loop remains unblocked.

    Parameters
    ----------
    system_prompt:
        Instruction context placed in the ``system`` field of the Nova
        messages-v1 request body.
    user_message:
        The user turn content.
    model_id:
        Bedrock model ID to use.  Defaults to ``settings.nova_model_id``
        (``amazon.nova-lite-v1:0``).
    max_tokens:
        Hard cap on the response length in tokens.
    temperature:
        Sampling temperature.  Lower = more deterministic.  For JSON output
        tasks use 0.0–0.2.

    Returns
    -------
    str
        The assistant text from the first content block.

    Raises
    ------
    ClientError / BotoCoreError
        Propagated from boto3 so callers can decide how to handle
        (skip / fallback).
    """
    resolved_model_id = model_id or settings.nova_model_id
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _invoke_sync,
        system_prompt,
        user_message,
        resolved_model_id,
        max_tokens,
        temperature,
    )


# ---------------------------------------------------------------------------
# Internal synchronous implementation
# ---------------------------------------------------------------------------

def _invoke_sync(
    system_prompt: str,
    user_message: str,
    model_id: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """Blocking Nova invocation — must be called from a thread, not the loop."""
    client = get_bedrock_client()

    body: dict[str, Any] = {
        "schemaVersion": "messages-v1",
        "messages": [
            {
                "role": "user",
                "content": [{"text": user_message}],
            }
        ],
        "system": [{"text": system_prompt}],
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    }

    logger.info(
        "Invoking Bedrock model %s (max_tokens=%d, temperature=%.2f)",
        model_id,
        max_tokens,
        temperature,
    )

    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
    except (ClientError, BotoCoreError):
        logger.exception("Bedrock invoke_model failed for model %s", model_id)
        raise

    result: dict[str, Any] = json.loads(response["body"].read())

    # Nova messages-v1 response shape:
    #   {"output": {"message": {"content": [{"text": "..."}]}}, ...}
    try:
        text: str = result["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(
            f"Unexpected Nova response shape — could not extract text: {result!r}"
        ) from exc

    logger.info(
        "Bedrock response received — stop_reason=%s, input_tokens=%s, output_tokens=%s",
        result.get("stopReason"),
        result.get("usage", {}).get("inputTokens"),
        result.get("usage", {}).get("outputTokens"),
    )

    return text


# ---------------------------------------------------------------------------
# JSON response parser helper
# ---------------------------------------------------------------------------

# Matches fenced code blocks:  ```json\n...\n```  or  ```\n...\n```
_FENCE_RE = re.compile(
    r"```(?:json)?\s*\n(.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)


def parse_json_response(text: str) -> dict[str, Any]:
    """Best-effort JSON extraction from a Nova response string.

    Strategy
    --------
    1. Direct ``json.loads`` on the full text (model returned bare JSON).
    2. Extract the first fenced code block and parse its contents.
    3. Find the first ``{`` … last ``}`` substring and attempt to parse it
       (handles leading/trailing prose around a JSON object).
    4. Log a warning and return ``{}`` if all strategies fail.

    Parameters
    ----------
    text:
        Raw string returned by ``invoke_nova``.

    Returns
    -------
    dict
        Parsed JSON object, or an empty dict on total failure.
    """
    # --- Strategy 1: bare JSON ------------------------------------------------
    stripped = text.strip()
    try:
        result = json.loads(stripped)
        if isinstance(result, dict):
            return result
        logger.warning(
            "parse_json_response: top-level JSON value is not an object (%s); "
            "returning empty dict",
            type(result).__name__,
        )
        return {}
    except json.JSONDecodeError:
        pass

    # --- Strategy 2: fenced code block ----------------------------------------
    match = _FENCE_RE.search(stripped)
    if match:
        candidate = match.group(1).strip()
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    # --- Strategy 3: first { … last } substring --------------------------------
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start : end + 1]
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    # --- Total failure ---------------------------------------------------------
    logger.warning(
        "parse_json_response: all extraction strategies failed — returning {}. "
        "First 200 chars of response: %r",
        text[:200],
    )
    return {}
