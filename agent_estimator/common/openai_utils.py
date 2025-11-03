"""OpenAI client helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import time
from typing import Any, Dict, List, Optional

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from .config import DEFAULT_MODEL

_client: Optional[OpenAI] = None


@dataclass
class TokenUsageDetail:
    label: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenUsageLog:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    requests: int = 0
    details: List[TokenUsageDetail] = field(default_factory=list)

    def copy(self) -> "TokenUsageLog":
        return TokenUsageLog(
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=self.total_tokens,
            requests=self.requests,
            details=[
                TokenUsageDetail(
                    label=detail.label,
                    prompt_tokens=detail.prompt_tokens,
                    completion_tokens=detail.completion_tokens,
                    total_tokens=detail.total_tokens,
                    metadata=dict(detail.metadata),
                )
                for detail in self.details
            ],
        )

    def stage_totals(self) -> Dict[str, Dict[str, int]]:
        stage_map: Dict[str, Dict[str, int]] = {}
        for detail in self.details:
            label = detail.label or "unspecified"
            bucket = stage_map.setdefault(
                label,
                {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "requests": 0},
            )
            bucket["prompt_tokens"] += detail.prompt_tokens
            bucket["completion_tokens"] += detail.completion_tokens
            bucket["total_tokens"] += detail.total_tokens
            bucket["requests"] += 1
        return stage_map


_token_usage = TokenUsageLog()


def reset_token_usage() -> None:
    """Reset accumulated token usage (e.g. between demographic runs)."""
    global _token_usage
    _token_usage = TokenUsageLog()


def get_token_usage_log() -> TokenUsageLog:
    """Return a snapshot of the current token usage log."""
    return _token_usage.copy()


def _usage_to_dict(usage: Any) -> Dict[str, Any]:
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return usage
    for attr in ("model_dump", "to_dict"):
        if hasattr(usage, attr):
            try:
                data = getattr(usage, attr)()
                if isinstance(data, dict):
                    return data
            except Exception:  # pragma: no cover - defensive, usage metadata best effort
                continue
    if hasattr(usage, "__dict__"):
        return dict(usage.__dict__)
    return {}


def _coerce_token_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return 0


def record_usage(usage: Any, label: Optional[str], metadata: Optional[Dict[str, Any]] = None) -> None:
    """Record token usage for a single API call."""
    usage_dict = _usage_to_dict(usage)
    if not usage_dict:
        return

    prompt = usage_dict.get("prompt_tokens") or usage_dict.get("input_tokens") or 0
    completion = usage_dict.get("completion_tokens") or usage_dict.get("output_tokens") or 0
    total = usage_dict.get("total_tokens") or 0

    prompt_tokens = _coerce_token_int(prompt)
    completion_tokens = _coerce_token_int(completion)
    total_tokens = _coerce_token_int(total) or (prompt_tokens + completion_tokens)

    detail_meta: Dict[str, Any] = {}
    if metadata:
        detail_meta = {str(k): v for k, v in metadata.items()}

    detail = TokenUsageDetail(
        label=label or "call",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        metadata=detail_meta,
    )

    _token_usage.details.append(detail)
    _token_usage.prompt_tokens += prompt_tokens
    _token_usage.completion_tokens += completion_tokens
    _token_usage.total_tokens += total_tokens
    _token_usage.requests += 1

    try:
        from pathlib import Path
        record = {
            "timestamp": time.time(),
            "label": detail.label,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "metadata": detail_meta,
        }
        Path("agent_estimator_token_log.jsonl").open("a", encoding="utf-8").write(json.dumps(record) + "\n")
    except Exception:
        pass


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _prepare_text_param(response_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Translate legacy response_format schema into Responses API text parameter."""
    if not response_schema:
        return None
    if response_schema.get("type") != "json_schema":
        return None
    json_schema = response_schema.get("json_schema", {})
    if not isinstance(json_schema, dict):
        return None
    name = json_schema.get("name", "structured_output")
    schema = json_schema.get("schema", {})
    if not schema:
        return None
    text_param: Dict[str, Any] = {
        "format": {
            "type": "json_schema",
            "name": name,
            "schema": schema,
        }
    }
    if json_schema.get("strict") is not None:
        text_param["format"]["strict"] = bool(json_schema["strict"])
    if description := json_schema.get("description"):
        text_param["format"]["description"] = description
    return text_param


def call_response_api(
    system_prompt: str,
    user_prompt: str,
    response_schema: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    top_p: float = 1.0,
    max_output_tokens: int = 400,
    seed: Optional[int] = None,
    usage_label: Optional[str] = None,
    usage_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    client = get_client()
    text_param = _prepare_text_param(response_schema or {})
    response_format = None
    if response_schema and response_schema.get("type") == "json_schema":
        json_schema = response_schema.get("json_schema", {})
        if isinstance(json_schema, dict) and json_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": json_schema,
            }
    selected_model = model or DEFAULT_MODEL
    no_sampling_prefixes = ("gpt-5", "o4")
    supports_sampling = True
    if selected_model:
        supports_sampling = not any(selected_model.startswith(prefix) for prefix in no_sampling_prefixes)

    kwargs: Dict[str, Any] = {}
    if text_param:
        kwargs["text"] = text_param
    if supports_sampling:
        kwargs["temperature"] = temperature
        kwargs["top_p"] = top_p
    effective_max_tokens = max_output_tokens
    kwargs["max_output_tokens"] = effective_max_tokens
    if seed is not None:
        kwargs["seed"] = seed

    def _invoke(current_user_prompt: str) -> tuple[str, Any]:
        try:
            responses_resource = getattr(client, "responses", None)
            if responses_resource and hasattr(responses_resource, "create"):
                resp = responses_resource.create(
                    model=selected_model,
                    input=[
                        {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                        {"role": "user", "content": [{"type": "input_text", "text": current_user_prompt}]},
                    ],
                    **kwargs,
                )
                status = getattr(resp, "status", "completed")
                if status != "completed":
                    incomplete = getattr(resp, "incomplete_details", None)
                    reason = getattr(incomplete, "reason", "")
                    raise RuntimeError(f"Model returned incomplete status: {reason}")
                text = None
                output_text = getattr(resp, "output_text", None)
                if output_text:
                    if isinstance(output_text, (list, tuple)):
                        text = next((str(item) for item in output_text if item), None)
                    else:
                        text = str(output_text)
                    if text is None:
                        output_items = getattr(resp, "output", []) or []
                        for item in output_items:
                            content = getattr(item, "content", None)
                            if not content:
                                continue
                            for chunk in content:
                                chunk_text = getattr(chunk, "text", None)
                                if chunk_text:
                                    text = str(chunk_text)
                                    break
                            if text:
                                break
                    if text is None:
                        try:
                            text = resp.output[0].content[0].text  # type: ignore[index]
                        except Exception:
                            text = None
                    if text is not None:
                        return text, getattr(resp, "usage", None)
                raise RuntimeError("Failed to parse response from model.")
            completion_kwargs: Dict[str, Any] = {
                "model": selected_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": current_user_prompt},
                ],
            }
            # GPT-5 and o4 models use max_completion_tokens instead of max_tokens
            max_tokens_value = kwargs.get("max_output_tokens", effective_max_tokens)
            if selected_model and any(selected_model.startswith(prefix) for prefix in ("gpt-5", "o4")):
                completion_kwargs["max_completion_tokens"] = max_tokens_value
            else:
                completion_kwargs["max_tokens"] = max_tokens_value

            if supports_sampling:
                completion_kwargs["temperature"] = kwargs.get("temperature", temperature)
                completion_kwargs["top_p"] = kwargs.get("top_p", top_p)
            if seed is not None:
                completion_kwargs["seed"] = seed
            if response_format:
                completion_kwargs["response_format"] = response_format
            try:
                resp = client.chat.completions.create(**completion_kwargs)
            except TypeError as exc:
                # Handle SDK not supporting certain parameters
                if response_format and "response_format" in str(exc):
                    completion_kwargs.pop("response_format", None)
                    resp = client.chat.completions.create(**completion_kwargs)
                elif "max_completion_tokens" in str(exc):
                    # Fallback: SDK doesn't support max_completion_tokens yet, use max_tokens instead
                    completion_kwargs.pop("max_completion_tokens", None)
                    completion_kwargs["max_tokens"] = max_tokens_value
                    resp = client.chat.completions.create(**completion_kwargs)
                else:
                    raise
            text = resp.choices[0].message.content  # type: ignore[index]
            return text, getattr(resp, "usage", None)
        except (APIConnectionError, RateLimitError, APIError) as exc:
            raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

    prompt_variants = [user_prompt]
    if response_schema:
        prompt_variants.append(
            f"{user_prompt}\n\nReturn ONLY a valid JSON object that satisfies the schema. Do not add commentary."
        )

    last_error: Optional[Exception] = None
    for variant_index, prompt_variant in enumerate(prompt_variants, start=1):
        try:
            content, usage = _invoke(prompt_variant)
            detail_meta = dict(usage_meta or {})
            detail_meta["prompt_variant"] = variant_index
            record_usage(usage, usage_label, detail_meta)
            return resp_parse_json(content or "")
        except Exception as exc:
            last_error = exc
            continue

    if last_error:
        raise last_error
    raise RuntimeError("Failed to obtain response from model.")


def resp_parse_json(raw: str) -> Dict[str, Any]:
    import json  # lazy import to avoid cost when unused

    if not raw:
        raise RuntimeError("Received empty response from model.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if 0 <= start < end:
            snippet = raw[start : end + 1]
            return json.loads(snippet)
        raise RuntimeError(f"Failed to decode JSON from model response: {raw}") from None
