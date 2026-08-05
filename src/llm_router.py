"""
llm_router.py — Production-Grade Fallback Routing Engine
=========================================================
Architecture:
    Primary:  Google Gemini 2.0 Flash  (via google-genai SDK)
    Fallback: Groq llama-3.3-70b-versatile (via groq SDK)
    Failsafe: Hardcoded French apology JSON

Routing Flow:
    1. Try Gemini with a configurable timeout.
    2. On ANY Gemini failure (429, 500, timeout, quota) → instantly
       reroute the full stateless chat history to Groq.
    3. On Groq failure (400 model_decommissioned, 429 rate limit) →
       return a hardcoded, valid JSON failsafe so the frontend
       never receives a null or broken response.

Environment Variables (Railway / .env):
    PRIMARY_API_KEY   — Google Gemini API key
    GROQ_API_KEY      — Groq API key

Usage (drop-in replacement for chat.send_message()):
    from llm_router import route_llm_request

    response_json = route_llm_request(
        system_prompt  = system_prompt_string,
        chat_history   = [{"role": "user", "parts": [...]}, ...],
        user_input     = "Je suis allé au le cinéma hier.",
        mentor_name    = "Derek"
    )
"""

import os
import time
import json
import re
import logging
from typing import Optional

# --- SDK Imports (lazy-fail gracefully if not installed) ---
try:
    from google import genai
    from google.genai import types as genai_types
    from google.genai.errors import APIError as GeminiAPIError
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False
    GeminiAPIError = Exception

try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False

# ============================================================
# CONFIGURATION
# ============================================================

PRIMARY_API_KEY   = os.environ.get("PRIMARY_API_KEY", "")
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")

# Primary Gemini model preference order (tries each before giving up)
GEMINI_MODELS     = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]

# Fallback Groq model (70B for pedagogical quality)
GROQ_MENTOR_MODEL = "llama-3.3-70b-versatile"

# Request timeout for Gemini calls (seconds).
# If Gemini hangs beyond this, we don't wait — we route to Groq immediately.
GEMINI_TIMEOUT_S  = 12.0

# Structured output keys the frontend contract requires
REQUIRED_JSON_KEYS = {"french_response", "mentor_feedback", "is_exit"}

logger = logging.getLogger(__name__)

# ============================================================
# FAILSAFE PAYLOAD
# Returned when BOTH Gemini AND Groq fail simultaneously.
# Guarantees the frontend/parser never receives null.
# ============================================================
FAILSAFE_RESPONSE = {
    "french_response": (
        "Désolé, je rencontre des difficultés techniques en ce moment. "
        "Peux-tu réessayer dans quelques instants ? Je suis toujours là pour toi !"
    ),
    "mentor_feedback": (
        "Both the primary API (Gemini) and the fallback API (Groq) are temporarily "
        "unavailable. This is likely a transient quota or network issue. "
        "Please wait 30 seconds and try again."
    ),
    "phonetic_breakdown": "",
    "internal_adaptation_level": "FAILSAFE",
    "is_exit": True,
    "new_vocabulary_introduced": [],
    "diagnostics": "DUAL_API_FAILURE"
}

# ============================================================
# UTILITIES
# ============================================================

def _extract_retry_seconds(error_message: str) -> Optional[float]:
    """Parse server-requested retry delay from error message text."""
    if not error_message:
        return None
    match = re.search(
        r'retry\s+(?:in|after)\s+(\d+(?:\.\d+)?)\s*s(?:ec(?:onds)?)?',
        str(error_message), re.IGNORECASE
    )
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def _clean_json_string(text: str) -> str:
    """Strip markdown code fences and whitespace from an LLM JSON string."""
    cleaned = str(text).strip()
    cleaned = re.sub(r'^```(?:json|JSON)?', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'```$', '', cleaned).strip()
    return cleaned


def _safe_parse_json(raw_text: str) -> dict:
    """
    Parse JSON from a raw LLM string.
    Tries strict parse first, then regex extraction as fallback.
    Returns {} on complete failure.
    """
    if not raw_text:
        return {}
    cleaned = _clean_json_string(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {}


def _validate_response(parsed: dict) -> bool:
    """Ensure the parsed dict contains all required contract keys."""
    return bool(parsed) and REQUIRED_JSON_KEYS.issubset(parsed.keys())


# ============================================================
# ROUTE 1: GEMINI PRIMARY ENGINE
# ============================================================

def _call_gemini(
    system_prompt: str,
    chat_history: list,
    user_input: str,
    timeout: float = GEMINI_TIMEOUT_S
) -> Optional[dict]:
    """
    Call Google Gemini 2.0 Flash with the full stateful chat history.
    Returns a parsed JSON dict on success, or None on any failure.
    
    The google-genai SDK manages stateful chat sessions internally,
    but we accept an explicit history array to support Railway cold-start
    scenarios where chat objects are rebuilt from serialized state.
    """
    if not _GEMINI_AVAILABLE or not PRIMARY_API_KEY:
        logger.warning("[LLM Router] Gemini SDK not available or PRIMARY_API_KEY missing. Skipping primary.")
        return None

    client = genai.Client(api_key=PRIMARY_API_KEY)

    for model_name in GEMINI_MODELS:
        try:
            logger.info(f"[LLM Router] Attempting Gemini primary via model: {model_name}")

            # Reconstruct stateless history for this call
            # Gemini SDK accepts history as a list of Content objects
            history_contents = []
            for turn in chat_history:
                role  = turn.get("role", "user")
                parts = turn.get("parts", [turn.get("content", "")])
                if isinstance(parts, str):
                    parts = [parts]
                history_contents.append(
                    genai_types.Content(
                        role=role,
                        parts=[genai_types.Part(text=p) for p in parts if isinstance(p, str)]
                    )
                )

            chat = client.chats.create(
                model=model_name,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.4,
                    response_mime_type="application/json",
                    http_options=genai_types.HttpOptions(timeout=int(timeout * 1000))
                ),
                history=history_contents
            )

            raw = chat.send_message(user_input).text
            parsed = _safe_parse_json(raw)

            if _validate_response(parsed):
                logger.info(f"[LLM Router] Gemini success via {model_name}.")
                return parsed

            logger.warning(f"[LLM Router] Gemini ({model_name}) returned invalid JSON shape: {raw[:120]}")

        except GeminiAPIError as e:
            code = getattr(e, 'code', '') or ''
            msg  = getattr(e, 'message', str(e))
            logger.warning(f"[LLM Router] Gemini APIError [{code}] on {model_name}: {msg[:100]}")

            # Honor server-requested retry delay before moving to next model attempt
            retry_s = _extract_retry_seconds(msg)
            if retry_s and retry_s < GEMINI_TIMEOUT_S:
                logger.info(f"[LLM Router] Server requests retry in {retry_s}s. Waiting...")
                time.sleep(retry_s + 1.0)
                continue  # retry same model once after server-requested delay

            # For hard quota errors (429, 503) don't retry — hand off to Groq
            if "429" in str(code) or "503" in str(code) or "quota" in msg.lower():
                logger.warning("[LLM Router] Gemini quota/rate-limit hit. Handing off to Groq fallback.")
                return None

        except Exception as e:
            is_timeout = "timeout" in str(e).lower() or "timed out" in str(e).lower()
            if is_timeout:
                logger.warning(f"[LLM Router] Gemini timed out after {timeout}s on {model_name}. Handing off to Groq.")
            else:
                logger.warning(f"[LLM Router] Gemini unexpected error on {model_name}: {type(e).__name__}: {str(e)[:100]}")
            return None

    logger.warning("[LLM Router] All Gemini models exhausted. Handing off to Groq fallback.")
    return None


# ============================================================
# ROUTE 2: GROQ FALLBACK ENGINE
# ============================================================

def _call_groq(
    system_prompt: str,
    chat_history: list,
    user_input: str
) -> Optional[dict]:
    """
    Stateless Groq fallback using llama-3.3-70b-versatile.
    
    Groq has NO memory between calls — the ENTIRE conversation history
    (system prompt + all prior turns + new user message) is passed in
    a single messages[] array on every request.
    
    Handles two Groq-specific failure modes:
    - HTTP 400: Model decommissioned → log and return None
    - HTTP 429: Rate limit (100k TPM) → short backoff, then return None
    """
    if not _GROQ_AVAILABLE or not GROQ_API_KEY:
        logger.warning("[LLM Router] Groq SDK not available or GROQ_API_KEY missing. Skipping fallback.")
        return None

    groq_client = Groq(api_key=GROQ_API_KEY)
    logger.info(f"[LLM Router] Attempting Groq fallback via {GROQ_MENTOR_MODEL}.")

    # ── Build the complete stateless messages payload ────────────────────
    # Groq requires the FULL conversation context in every single call.
    messages = [{"role": "system", "content": system_prompt}]

    for turn in chat_history:
        role = turn.get("role", "user")
        # Normalize Gemini "parts" format → plain string content for Groq
        parts = turn.get("parts", None)
        if parts is not None:
            content = " ".join(p for p in parts if isinstance(p, str))
        else:
            content = turn.get("content", "")
        if content:
            messages.append({"role": role, "content": content})

    # Append the new user message
    messages.append({"role": "user", "content": user_input})

    for attempt in range(1, 4):
        try:
            completion = groq_client.chat.completions.create(
                messages=messages,
                model=GROQ_MENTOR_MODEL,
                temperature=0.3,
                response_format={"type": "json_object"},
                timeout=15.0
            )
            raw = completion.choices[0].message.content
            parsed = _safe_parse_json(raw)

            if _validate_response(parsed):
                logger.info(f"[LLM Router] Groq fallback success on attempt {attempt}.")
                return parsed

            logger.warning(f"[LLM Router] Groq returned invalid JSON shape: {raw[:120]}")
            return None

        except Exception as e:
            err_str = str(e)
            err_code = ""
            # Extract HTTP status from Groq SDK error string
            code_match = re.search(r'status_code=(\d+)|Error code:\s*(\d+)', err_str)
            if code_match:
                err_code = code_match.group(1) or code_match.group(2)

            # ── Groq-specific error: Model decommissioned (HTTP 400) ──────
            if "400" in err_code or "model_decommissioned" in err_str.lower():
                logger.error(
                    f"[LLM Router] GROQ CRITICAL: Model '{GROQ_MENTOR_MODEL}' is decommissioned (HTTP 400). "
                    "Update GROQ_MENTOR_MODEL in llm_router.py. Activating failsafe."
                )
                return None  # Skip remaining attempts — model is gone

            # ── Groq-specific error: Rate limit / 100k TPM exceeded (HTTP 429) ──
            elif "429" in err_code or "rate_limit" in err_str.lower() or "token" in err_str.lower():
                retry_s = _extract_retry_seconds(err_str) or (3.0 * attempt)
                logger.warning(
                    f"[LLM Router] Groq rate limit hit (100k TPM). "
                    f"Waiting {retry_s:.1f}s before retry (attempt {attempt}/3)..."
                )
                if attempt < 3:
                    time.sleep(retry_s)
                    continue
                else:
                    logger.error("[LLM Router] Groq rate limit persists after 3 retries. Activating failsafe.")
                    return None

            # ── Groq timeout or generic network error ────────────────────
            elif "timeout" in err_str.lower():
                logger.warning(f"[LLM Router] Groq timed out on attempt {attempt}.")
                if attempt < 3:
                    time.sleep(2.0 * attempt)
                    continue
                return None

            else:
                logger.error(f"[LLM Router] Groq unexpected error on attempt {attempt}: {err_str[:200]}")
                return None

    return None


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def route_llm_request(
    system_prompt: str,
    chat_history: list,
    user_input: str,
    mentor_name: str = "Mentor"
) -> str:
    """
    Primary public interface for all LLM calls in Linguaphantom.
    
    Drop-in replacement for `chat.send_message(user_input).text`.
    Returns a JSON string guaranteed to be valid (never null).

    Routing priority:
        1. Gemini 2.0 Flash (PRIMARY_API_KEY) with GEMINI_TIMEOUT_S timeout
        2. Groq llama-3.3-70b-versatile (GROQ_API_KEY) — stateless full history
        3. FAILSAFE_RESPONSE — hardcoded French apology, is_exit: true

    Args:
        system_prompt (str):  The full mentor system prompt string.
        chat_history  (list): List of prior turns in Gemini Content format.
                              [{"role": "user", "parts": ["..."]},
                               {"role": "model", "parts": ["..."]}]
        user_input    (str):  The current user message string.
        mentor_name   (str):  Used for logging and failsafe metadata.

    Returns:
        str: A JSON-formatted string with at minimum:
             {"french_response": ..., "mentor_feedback": ..., "is_exit": ...}
    """
    logger.info(f"[LLM Router] Routing request for mentor '{mentor_name}' | Input: {user_input[:60]}...")

    # ── Route 1: Gemini Primary ──────────────────────────────────────────
    result = _call_gemini(system_prompt, chat_history, user_input, timeout=GEMINI_TIMEOUT_S)

    if result is not None:
        return json.dumps(result, ensure_ascii=False)

    # ── Route 2: Groq Fallback ───────────────────────────────────────────
    logger.warning(f"[LLM Router] Gemini failed for '{mentor_name}'. Routing to Groq fallback...")
    result = _call_groq(system_prompt, chat_history, user_input)

    if result is not None:
        result["diagnostics"] = "GROQ_FALLBACK_ACTIVATED"
        return json.dumps(result, ensure_ascii=False)

    # ── Route 3: Dual Failsafe ───────────────────────────────────────────
    logger.error(
        f"[LLM Router] CRITICAL: Both Gemini AND Groq failed for '{mentor_name}'. "
        "Returning hardcoded failsafe. Check API keys and quotas immediately."
    )
    failsafe = {**FAILSAFE_RESPONSE, "diagnostics": f"DUAL_API_FAILURE:{mentor_name}"}
    return json.dumps(failsafe, ensure_ascii=False)
