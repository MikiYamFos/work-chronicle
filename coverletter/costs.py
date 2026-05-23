from __future__ import annotations

# Short aliases → canonical model IDs
MODEL_ALIASES: dict[str, str] = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-7",
}

# Prices per million tokens (input, output). Verify at https://www.anthropic.com/pricing
_PRICES: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-7": (15.00, 75.00),
}


def resolve_model(name: str) -> str:
    return MODEL_ALIASES.get(name.lower(), name)


def _price(model: str) -> tuple[float, float] | None:
    for key, price in _PRICES.items():
        if key in model.lower() or model.lower() in key:
            return price
    return None


# --- Session accumulator ---

_session_input_tokens: int = 0
_session_output_tokens: int = 0
_session_cost: float = 0.0
_last_cost: float = 0.0


def supports_temperature(model: str) -> bool:
    """Returns False for models that have deprecated the temperature parameter."""
    _no_temp = {"claude-opus-4"}
    return not any(m in model.lower() for m in _no_temp)


def record(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> float:
    global _session_input_tokens, _session_output_tokens, _session_cost, _last_cost
    _session_input_tokens += input_tokens + cache_creation_tokens + cache_read_tokens
    _session_output_tokens += output_tokens
    price = _price(model)
    if price:
        input_price, output_price = price
        cost = (
            (input_tokens / 1_000_000) * input_price
            + (output_tokens / 1_000_000) * output_price
            + (cache_creation_tokens / 1_000_000) * input_price * 1.25  # write: 25% more
            + (cache_read_tokens / 1_000_000) * input_price * 0.10     # read: 90% discount
        )
        _session_cost += cost
        _last_cost = cost
        return cost
    _last_cost = 0.0
    return 0.0


def step_cost() -> str:
    """Cost of the most recent step — for inline display after each API call."""
    if _last_cost:
        return f"~${_last_cost:.4f}"
    return ""


def running_total() -> str:
    """Running session total — shown after each major step."""
    if not _session_cost:
        return ""
    return f"~${_session_cost:.4f} session"


def session_summary() -> str:
    if not _session_input_tokens and not _session_output_tokens:
        return ""
    parts = [f"{_session_input_tokens:,} in / {_session_output_tokens:,} out tokens"]
    if _session_cost:
        parts.append(f"~${_session_cost:.4f}")
    return "  ".join(parts)
