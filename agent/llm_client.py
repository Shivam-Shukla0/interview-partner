"""Thin wrapper around the Anthropic client."""
import logging
import time

import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self._client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    def complete(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int,
    ) -> str:
        """Simple text completion. Returns the assistant's text."""
        response = self._call_with_retry(
            system=system,
            messages=messages,
            max_tokens=max_tokens,
        )
        text = response.content[0].text
        logger.debug(
            "complete: input=%d output=%d tokens",
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        return text

    def complete_structured(
        self,
        system: str,
        messages: list[dict],
        schema_tool: dict,
        max_tokens: int,
    ) -> dict:
        """Structured output via tool-use. Returns the tool input dict."""
        response = self._call_with_retry(
            system=system,
            messages=messages,
            max_tokens=max_tokens,
            tools=[schema_tool],
            tool_choice={"type": "tool", "name": schema_tool["name"]},
        )
        for block in response.content:
            if block.type == "tool_use":
                logger.debug(
                    "complete_structured: input=%d output=%d tokens",
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                )
                return block.input
        raise ValueError("No tool_use block in response")

    def _call_with_retry(self, **kwargs) -> anthropic.types.Message:
        import config
        try:
            return self._client.messages.create(model=config.MODEL_NAME, **kwargs)
        except anthropic.RateLimitError:
            logger.warning("Rate limit hit — retrying in 2s")
            time.sleep(2)
            return self._client.messages.create(model=config.MODEL_NAME, **kwargs)
