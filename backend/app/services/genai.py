"""Unified GenAI service — Gemini Pro for narratives, NVIDIA NIM for code/analysis.

Provides a single `generate()` function with automatic fallback to deterministic
templates if API keys are missing, rate-limited, or the service is unreachable.
"""
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("autopilot.genai")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# Gemini REST endpoint (v1beta)
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
    "/models/gemini-2.0-flash-lite:generateContent"
)

# NVIDIA NIM endpoint (Llama 3.1 70B)
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"

_http = httpx.AsyncClient(timeout=45.0)


# ─── Gemini ──────────────────────────────────────────────────────────────────

async def gemini_generate(
    prompt: str,
    *,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str | None:
    """Call Google Gemini and return the text response, or None on failure."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — skipping Gemini call")
        return None

    contents: list[dict[str, Any]] = []
    if system:
        contents.append({"role": "user", "parts": [{"text": system}]})
        contents.append(
            {"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]}
        )
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    body = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    try:
        resp = await _http.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=body,
        )
        if resp.status_code != 200:
            logger.error(
                "Gemini API returned %s: %s", resp.status_code, resp.text[:500]
            )
            return None
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            return parts[0].get("text", "") if parts else None
        return None
    except Exception:
        logger.exception("Gemini API call failed")
        return None


# ─── NVIDIA NIM ──────────────────────────────────────────────────────────────

async def nvidia_generate(
    prompt: str,
    *,
    system: str = "",
    temperature: float = 0.6,
    max_tokens: int = 1024,
) -> str | None:
    """Call NVIDIA NIM (Llama 3.1 70B) and return the text, or None on failure."""
    if not NVIDIA_API_KEY:
        logger.warning("NVIDIA_API_KEY not set — skipping NVIDIA call")
        return None

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": NVIDIA_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        resp = await _http.post(
            NVIDIA_URL,
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
            json=body,
        )
        if resp.status_code != 200:
            logger.error(
                "NVIDIA API returned %s: %s", resp.status_code, resp.text[:500]
            )
            return None
        data = resp.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return None
    except Exception:
        logger.exception("NVIDIA NIM API call failed")
        return None


# ─── Unified entry point ─────────────────────────────────────────────────────

async def generate(
    prompt: str,
    *,
    system: str = "",
    provider: str = "gemini",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    fallback: str = "",
) -> str:
    """Generate text with automatic provider fallback.

    Args:
        prompt: The user prompt.
        system: System instruction for context.
        provider: Preferred provider ("gemini" or "nvidia").
        temperature: Sampling temperature.
        max_tokens: Max output length.
        fallback: Static text to return if all providers fail.

    Returns:
        Generated text, or the fallback string.
    """
    # Try preferred provider first
    if provider == "gemini":
        result = await gemini_generate(
            prompt, system=system, temperature=temperature, max_tokens=max_tokens,
        )
        if result:
            return result
        # Fallback to NVIDIA
        result = await nvidia_generate(
            prompt, system=system, temperature=temperature, max_tokens=max_tokens,
        )
        if result:
            return result
    else:
        result = await nvidia_generate(
            prompt, system=system, temperature=temperature, max_tokens=max_tokens,
        )
        if result:
            return result
        # Fallback to Gemini
        result = await gemini_generate(
            prompt, system=system, temperature=temperature, max_tokens=max_tokens,
        )
        if result:
            return result

    logger.warning("All GenAI providers failed — using fallback text")
    return fallback
