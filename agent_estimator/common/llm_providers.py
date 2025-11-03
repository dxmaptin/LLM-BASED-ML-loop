"""Multi-provider LLM client supporting OpenAI, Gemini, and Claude APIs."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from dataclasses import dataclass

# Import existing utilities
from .openai_utils import record_usage, TokenUsageLog


@dataclass
class LLMResponse:
    """Unified response format from any LLM provider."""
    content: str
    usage: Optional[Any] = None
    provider: str = "openai"


def call_openai_api(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float = 0.1,
    top_p: float = 1.0,
    max_tokens: int = 400,
    seed: Optional[int] = None,
) -> LLMResponse:
    """Call OpenAI API (existing implementation)."""
    from openai import OpenAI, APIConnectionError, APIError, RateLimitError

    client = OpenAI()

    try:
        # Handle GPT-5 and o4 models differently
        no_sampling_prefixes = ("gpt-5", "o4")
        supports_sampling = not any(model.startswith(prefix) for prefix in no_sampling_prefixes)

        completion_kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        # Max tokens parameter
        if model and any(model.startswith(prefix) for prefix in ("gpt-5", "o4")):
            completion_kwargs["max_completion_tokens"] = max_tokens
        else:
            completion_kwargs["max_tokens"] = max_tokens

        # Sampling parameters
        if supports_sampling:
            completion_kwargs["temperature"] = temperature
            completion_kwargs["top_p"] = top_p

        if seed is not None:
            completion_kwargs["seed"] = seed

        resp = client.chat.completions.create(**completion_kwargs)
        content = resp.choices[0].message.content or ""

        return LLMResponse(
            content=content,
            usage=getattr(resp, "usage", None),
            provider="openai"
        )

    except (APIConnectionError, RateLimitError, APIError) as exc:
        raise RuntimeError(f"OpenAI API call failed: {exc}") from exc


def call_gemini_api(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float = 0.1,
    top_p: float = 1.0,
    max_tokens: int = 400,
    seed: Optional[int] = None,
) -> LLMResponse:
    """Call Google Gemini API."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError(
            "google-generativeai package not installed. "
            "Install with: pip install google-generativeai"
        )

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set. "
            "Get your API key from: https://aistudio.google.com/app/apikey"
        )

    genai.configure(api_key=api_key)

    # Map model names
    if model == "gemini-2.0-flash":
        gemini_model = "gemini-2.0-flash-exp"
    elif model == "gemini-1.5-pro":
        gemini_model = "gemini-1.5-pro"
    else:
        gemini_model = model  # Use as-is

    try:
        client = genai.GenerativeModel(
            model_name=gemini_model,
            system_instruction=system_prompt,
        )

        generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "max_output_tokens": max_tokens,
        }

        response = client.generate_content(
            user_prompt,
            generation_config=generation_config,
        )

        content = response.text

        # Extract usage stats
        usage_metadata = getattr(response, "usage_metadata", None)
        usage_dict = {}
        if usage_metadata:
            usage_dict = {
                "prompt_tokens": getattr(usage_metadata, "prompt_token_count", 0),
                "completion_tokens": getattr(usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(usage_metadata, "total_token_count", 0),
            }

        return LLMResponse(
            content=content,
            usage=usage_dict,
            provider="gemini"
        )

    except Exception as exc:
        raise RuntimeError(f"Gemini API call failed: {exc}") from exc


def call_claude_api(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float = 0.1,
    top_p: float = 1.0,
    max_tokens: int = 400,
    seed: Optional[int] = None,
) -> LLMResponse:
    """Call Anthropic Claude API."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "anthropic package not installed. "
            "Install with: pip install anthropic"
        )

    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable not set. "
            "Get your API key from: https://console.anthropic.com/"
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Map model names
    if model == "claude-3.5-sonnet" or model == "claude-sonnet":
        claude_model = "claude-3-5-sonnet-20241022"
    elif model == "claude-3-opus":
        claude_model = "claude-3-opus-20240229"
    elif model == "claude-3-haiku":
        claude_model = "claude-3-haiku-20240307"
    else:
        claude_model = model  # Use as-is

    # Add explicit JSON instruction to user prompt
    json_instruction = "\n\nYou MUST respond with ONLY a valid JSON object in this exact format (no additional text):\n{\n  \"distribution\": {\n    \"strongly_agree\": <number 0-100>,\n    \"slightly_agree\": <number 0-100>,\n    \"neither\": <number 0-100>,\n    \"slightly_disagree\": <number 0-100>,\n    \"strongly_disagree\": <number 0-100>\n  },\n  \"confidence\": <number 0.0-1.0>,\n  \"rationale\": \"<brief explanation>\"\n}\n\nThe distribution percentages must sum to 100. Return ONLY the JSON, no other text."

    enhanced_user_prompt = user_prompt + json_instruction

    try:
        response = client.messages.create(
            model=claude_model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            system=system_prompt,
            messages=[
                {"role": "user", "content": enhanced_user_prompt}
            ]
        )

        # Extract text content
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        # Extract usage stats
        usage_dict = {}
        if hasattr(response, "usage"):
            usage = response.usage
            usage_dict = {
                "prompt_tokens": getattr(usage, "input_tokens", 0),
                "completion_tokens": getattr(usage, "output_tokens", 0),
                "total_tokens": getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0),
            }

        return LLMResponse(
            content=content,
            usage=usage_dict,
            provider="claude"
        )

    except Exception as exc:
        raise RuntimeError(f"Claude API call failed: {exc}") from exc


def call_llm_provider(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float = 0.1,
    top_p: float = 1.0,
    max_tokens: int = 400,
    seed: Optional[int] = None,
    usage_label: Optional[str] = None,
    usage_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Unified interface to call any supported LLM provider.

    Automatically detects provider from model name:
    - OpenAI: gpt-4o, gpt-4, gpt-5, o4-*
    - Gemini: gemini-*
    - Claude: claude-*

    Returns parsed JSON response.
    """
    model_lower = model.lower()

    # Detect provider from model name
    if model_lower.startswith("gemini"):
        response = call_gemini_api(
            system_prompt, user_prompt, model, temperature, top_p, max_tokens, seed
        )
    elif model_lower.startswith("claude"):
        response = call_claude_api(
            system_prompt, user_prompt, model, temperature, top_p, max_tokens, seed
        )
    else:
        # Default to OpenAI
        response = call_openai_api(
            system_prompt, user_prompt, model, temperature, top_p, max_tokens, seed
        )

    # Record usage
    if response.usage:
        detail_meta = dict(usage_meta or {})
        detail_meta["provider"] = response.provider
        record_usage(response.usage, usage_label, detail_meta)

    # Parse JSON from response
    content = response.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks or surrounding text
        start = content.find("{")
        end = content.rfind("}")
        if 0 <= start < end:
            snippet = content[start : end + 1]
            return json.loads(snippet)
        raise RuntimeError(f"Failed to decode JSON from model response: {content}") from None
