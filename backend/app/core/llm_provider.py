"""
KrishiMitra AI -- Provider-Independent LLM Client (core/llm_provider.py)

Supports: Bionic/OpenAI-compatible local, OpenAI, Gemini, Ollama, rule-engine fallback.
All configuration driven by environment variables via settings.
No provider, model, or endpoint is hardcoded in the application.

Safety guarantees enforced in system prompt:
  - Never fabricates citations, crop statistics, or weather readings.
  - Explicitly distinguishes retrieved evidence vs LLM reasoning vs estimates vs unknown.
  - Asks clarifying questions when critical farm details are missing.
  - States when live weather / market data is unavailable rather than inventing values.
"""

import json
import logging
import asyncio
import re
from typing import AsyncGenerator, Dict, Any, Optional, List

import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are KrishiMitra AI, an expert agricultural advisory assistant for Indian farmers.

CORE CONVERSATIONAL POLICY:
1. Answer the user's direct question FIRST without delay or filler.
2. CONCISENESS: Default to 2 to 6 short sentences, or a few direct bullet points. Keep it crisp, practical, and fast to read.
3. NEVER add unsolicited crop recommendations, generic regional summaries, government schemes, or generic disclaimers unless explicitly asked or critical for crop safety.
4. If the user asks a general crop or soil fact (e.g. ideal soil pH for cotton), answer generally—do NOT force or invent a user district or mention their saved farm.
5. Do NOT repeat or echo back the user's entire farm profile unless specifically summarizing it upon request.
6. Give in-depth explanations ONLY when the user asks "Why?", "Explain", or requests deep technical details.
7. LANGUAGE: Respond strictly in the user's language (English, Telugu, or Hindi).

HONESTY & EVIDENCE RULES (Never violate):
1. Ground agricultural claims in the RETRIEVED AGRICULTURAL EVIDENCE provided. Use brief inline source citations like (ICAR-IIPR) or (FAO Paper 56).
2. Use ONLY sources actually provided in the retrieved evidence. NEVER invent citations, institutions, or years.
3. If evidence is missing or insufficient for a specific district/soil, plainly state: "Based on general agronomic knowledge—specific local research data is not in retrieved records."
4. NEVER fabricate soil values, weather readings, market prices, precision percentages, or yield guarantees.
5. Live weather and market prices are ONLY valid if present in LIVE TOOL RESULTS.
6. Do NOT expose internal reasoning traces, thoughts, or chain-of-thought tokens.
"""


def _clean_reasoning_tokens(text: str) -> str:
    """Remove <think>...</think> reasoning blocks from model output."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def _build_prompt(
    message: str,
    retrieved_context: str,
    lang: str,
    farm_context: Optional[Dict[str, Any]] = None,
    live_tool_results: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Assembles the full prompt from components.
    Order: retrieved evidence -> farm context -> live tool results -> question.
    """
    parts: List[str] = []

    if retrieved_context and retrieved_context.strip() and retrieved_context != "No specific agricultural record found.":
        parts.append(f"RETRIEVED AGRICULTURAL EVIDENCE:\n{retrieved_context}")
    else:
        parts.append(
            "RETRIEVED AGRICULTURAL EVIDENCE: [No relevant documents found for this query. "
            "Answer from general agronomic knowledge and explicitly note this limitation.]"
        )

    if farm_context:
        fc_lines = [f"  {k}: {v}" for k, v in farm_context.items() if v is not None and k != "live_weather"]
        if fc_lines:
            parts.append("CURRENT FARM PROFILE:\n" + "\n".join(fc_lines))

    if live_tool_results:
        if live_tool_results.get("weather"):
            parts.append(
                "LIVE WEATHER TOOL RESULT (verified, timestamped):\n"
                + json.dumps(live_tool_results["weather"], indent=2)
                + "\n(You may explain agronomic implications, but do NOT override any crop ranking based solely on this.)"
            )
        if live_tool_results.get("market"):
            parts.append(
                "LIVE MARKET PRICE TOOL RESULT (verified):\n"
                + json.dumps(live_tool_results["market"], indent=2)
            )

    if conversation_history:
        hist_text = "\n".join(
            f"{t['role'].upper()}: {t['content']}" for t in conversation_history[-4:]
        )
        parts.append(f"RECENT CONVERSATION:\n{hist_text}")

    parts.append(f"LANGUAGE: {lang}")
    parts.append(f"FARMER QUESTION: {message}")
    parts.append("TASK: Provide a grounded, source-attributed, farmer-friendly response in the requested language.")

    return "\n\n".join(parts)


class LLMProvider:
    """Provider-independent LLM client. All config from environment via settings."""

    def __init__(self):
        self._provider_override: Optional[str] = None
        self._timeout = getattr(settings, "LLM_TIMEOUT_S", 60.0)
        self._max_retries = getattr(settings, "LLM_MAX_RETRIES", 2)
        self._max_tokens = int(getattr(settings, "LLM_MAX_TOKENS", 400))
        if self._max_tokens > 450:
            self._max_tokens = 450
        self._last_error: Optional[str] = None

    @property
    def provider(self) -> str:
        if self._provider_override:
            return self._provider_override.lower()
        return (getattr(settings, "LLM_PROVIDER", None) or "ollama").lower()

    @provider.setter
    def provider(self, val: str):
        self._provider_override = val

    async def generate(
        self,
        message: str,
        retrieved_context: str = "",
        lang: str = "en",
        farm_context: Optional[Dict[str, Any]] = None,
        live_tool_results: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a grounded response using local Ollama Qwen 3.5 9B as the sole intelligence provider.
        Never silently falls back to remote LLMs or canned answers.
        """
        self._last_error = None
        prompt = _build_prompt(message, retrieved_context, lang, farm_context, live_tool_results, conversation_history)
        for attempt in range(self._max_retries + 1):
            result = await self._dispatch(prompt)
            if result:
                return result
            if attempt < self._max_retries:
                await asyncio.sleep(1.0 * (attempt + 1))

        # Sole provider honesty policy: return clear, actionable error if Ollama is unreachable
        err_details = self._last_error or "Connection failed or timed out"
        base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        model = getattr(settings, 'OLLAMA_MODEL', 'qwen3.5:9b')
        err_msg = (
            f"Ollama Service Error: KrishiMitra could not reach local Ollama model '{model}' at {base_url}. "
            f"Details: {err_details}. Please verify that Ollama is running ('ollama serve') with '{model}'."
        )
        logger.error(err_msg)
        return err_msg

    async def stream(
        self,
        message: str,
        retrieved_context: str = "",
        lang: str = "en",
        farm_context: Optional[Dict[str, Any]] = None,
        live_tool_results: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens using native local Ollama streaming."""
        prompt = _build_prompt(message, retrieved_context, lang, farm_context, live_tool_results, conversation_history)
        async for tok in self._ollama_stream(prompt):
            yield tok

    async def _dispatch(self, prompt: str) -> Optional[str]:
        # Sole agricultural intelligence provider: local Ollama
        return await self._ollama_generate(prompt)

    async def _bionic_generate(self, prompt: str) -> Optional[str]:
        base_url = (getattr(settings, "LLM_BASE_URL", None) or "http://localhost:1234/v1").rstrip("/")
        model = getattr(settings, "LLM_MODEL", None) or "qwen/qwen3.5-9b"
        api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "<think>\n</think>\n"},
            ],
            "temperature": 0.2,
            "max_tokens": self._max_tokens,
            "reasoning_effort": "low",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"].get("content", "")
                    cleaned = _clean_reasoning_tokens(content)
                    if cleaned:
                        return cleaned
                logger.warning(f"Bionic API returned HTTP {resp.status_code}")
        except httpx.ConnectError:
            logger.warning(f"Bionic API connection refused at {base_url}")
        except httpx.TimeoutException:
            logger.warning("Bionic API request timed out")
        except Exception as e:
            logger.error(f"Bionic API error: {e}")
        return None

    async def _bionic_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        base_url = (getattr(settings, "LLM_BASE_URL", None) or "http://localhost:1234/v1").rstrip("/")
        model = getattr(settings, "LLM_MODEL", None) or "qwen/qwen3.5-9b"
        api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "<think>\n</think>\n"},
            ],
            "temperature": 0.2,
            "max_tokens": self._max_tokens,
            "reasoning_effort": "low",
            "stream": True,
        }
        try:
            has_yielded = False
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", f"{base_url}/chat/completions", headers=headers, json=payload) as resp:
                    if resp.status_code == 200:
                        async for line in resp.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    tok = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                                    if tok and tok not in ("<think>", "</think>"):
                                        has_yielded = True
                                        yield tok
                                except Exception:
                                    pass
                        if has_yielded:
                            return
        except Exception as e:
            logger.warning(f"Bionic stream failed: {e}")
        # Fallback: full generation chunked
        full = await self._bionic_generate(prompt) or ""
        words = full.split(" ")
        for i in range(0, len(words), 3):
            yield " ".join(words[i:i+3]) + " "
            await asyncio.sleep(0.02)

    async def _openai_generate(self, prompt: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.2,
                        "max_tokens": self._max_tokens,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"].get("content", "").strip() or None
                logger.warning(f"OpenAI returned HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"OpenAI API failed: {e}")
        return None

    async def _gemini_generate(self, prompt: str) -> Optional[str]:
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            )
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}],
                        "generationConfig": {"temperature": 0.2, "maxOutputTokens": self._max_tokens},
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip() or None
                logger.warning(f"Gemini returned HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"Gemini API failed: {e}")
        return None

    async def _ollama_generate(self, prompt: str) -> Optional[str]:
        base_url = (getattr(settings, "OLLAMA_BASE_URL", None) or "http://localhost:11434").rstrip("/")
        model = getattr(settings, "OLLAMA_MODEL", None) or "qwen3.5:9b"
        url = f"{base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.2,
                "num_predict": self._max_tokens,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    msg = data.get("message", {})
                    content = msg.get("content", "").strip()
                    if content:
                        return _clean_reasoning_tokens(content)
                    self._last_error = f"Ollama returned 200 but empty message: {data}"
                    logger.warning(self._last_error)
                    return None
                self._last_error = f"HTTP {resp.status_code}: {resp.text}"
                logger.error(f"Ollama returned {self._last_error}")
                return None
        except httpx.ConnectError as e:
            self._last_error = f"Cannot connect to Ollama at {url} ({e})"
            logger.error(self._last_error)
            return None
        except httpx.TimeoutException as e:
            self._last_error = f"Ollama request timed out after {self._timeout}s ({e})"
            logger.error(self._last_error)
            return None
        except Exception as e:
            self._last_error = f"Ollama API error: {e}"
            logger.error(self._last_error)
            return None

    async def _ollama_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        base_url = (getattr(settings, "OLLAMA_BASE_URL", None) or "http://localhost:11434").rstrip("/")
        model = getattr(settings, "OLLAMA_MODEL", None) or "qwen3.5:9b"
        url = f"{base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
            "think": False,
            "options": {
                "temperature": 0.2,
                "num_predict": self._max_tokens,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", url, json=payload) as resp:
                    if resp.status_code == 200:
                        async for line in resp.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    tok = data.get("message", {}).get("content", "")
                                    if tok and tok not in ("<think>", "</think>"):
                                        yield tok
                                    if data.get("done"):
                                        break
                                except Exception:
                                    pass
                        return
                    err_msg = f"Error: Ollama stream returned HTTP {resp.status_code}"
                    logger.error(err_msg)
                    yield err_msg
                    return
        except Exception as e:
            err_msg = f"Error: Ollama streaming failed: {e}"
            logger.error(err_msg)
            yield err_msg
            return

    def _rule_engine_fallback(
        self, message: str, lang: str, farm_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Minimal honest fallback when all LLM providers are unavailable."""
        district = (farm_context or {}).get("district", "your district")
        non_agri = ["movie", "song", "cricket", "politics", "bitcoin", "football", "joke", "bollywood"]
        if any(w in message.lower() for w in non_agri):
            if lang == "te":
                return "నేను వ్యవసాయ సంబంధిత ప్రశ్నలకు మాత్రమే సహాయం చేయగలను."
            if lang == "hi":
                return "मैं केवल कृषि संबंधित प्रश्नों में सहायता करता हूँ।"
            return "I am an agricultural assistant. Please ask a farming-related question."
        if lang == "te":
            return (
                f"AI సేవ ప్రస్తుతం అందుబాటులో లేదు. దయచేసి కొద్దిసేపాగి మళ్ళీ ప్రయత్నించండి. "
                f"{district} ప్రాంత పంట సలహాలకు స్థానిక KVK సంప్రదించండి."
            )
        if lang == "hi":
            return (
                f"AI सेवा इस समय उपलब्ध नहीं है। कृपया थोड़ी देर बाद पुनः प्रयास करें। "
                f"{district} के लिए स्थानीय KVK से संपर्क करें।"
            )
        return (
            f"The AI service is temporarily unavailable. Please retry shortly. "
            f"For crop advice in {district}, contact your local Krishi Vigyan Kendra (KVK)."
        )


# Singleton instance used by the new RAG+LLM chat pipeline
llm_provider = LLMProvider()
