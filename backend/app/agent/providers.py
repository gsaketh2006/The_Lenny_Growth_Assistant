import os
import json
import time
import re
import uuid
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.schemas import ProviderInfo



class BaseLLMClient(ABC):
    """Abstract interface for LLM providers."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> AsyncGenerator[str, None]:
        """Yields text tokens as they are generated."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> str:
        """Generates a full response string."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Checks if the provider endpoint/keys are configured and healthy."""
        pass


# -------------------------------------------------------------------------
# Ollama Client (Local Default)
# -------------------------------------------------------------------------

class OllamaClient(BaseLLMClient):
    """Local Ollama client using native streaming API with auto-discovery of installed models."""

    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(model_name or settings.OLLAMA_MODEL)
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

    async def get_installed_models(self) -> List[str]:
        """Fetches list of model tags actually downloaded into the local Ollama instance."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return [m["name"] for m in data.get("models", []) if "name" in m]
        except Exception:
            pass
        return []

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/chat"
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        target_model = self.model_name
        payload = {
            "model": target_model,
            "messages": payload_messages,
            "options": {"temperature": temperature},
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream("POST", url, json=payload) as stream_resp:
                    if stream_resp.status_code == 404:
                        # Model not found in Ollama - check installed models
                        installed = await self.get_installed_models()
                        if installed:
                            fallback_model = installed[0]
                            logger.info(f"Ollama model '{target_model}' not found. Auto-falling back to installed model '{fallback_model}'")
                            yield f"*(Auto-switched to installed model `{fallback_model}`)*\n\n"
                            payload["model"] = fallback_model
                            async with client.stream("POST", url, json=payload) as fallback_resp:
                                if fallback_resp.status_code == 200:
                                    async for line in fallback_resp.aiter_lines():
                                        if line:
                                            try:
                                                data = json.loads(line)
                                                content = data.get("message", {}).get("content", "")
                                                if content:
                                                    yield content
                                                if data.get("done", False):
                                                    break
                                            except json.JSONDecodeError:
                                                continue
                                    return
                        
                        # If no installed model worked, give clear actionable steps
                        installed_str = f"Your installed models: {', '.join([f'`{m}`' for m in installed])}" if installed else "No models currently installed in Ollama."
                        yield (
                            f"⚠️ **Local Ollama Model Not Found**\n\n"
                            f"Ollama is running at `{self.base_url}`, but `{target_model}` is not installed.\n\n"
                            f"📌 {installed_str}\n\n"
                            f"**Quick Fix:**\n"
                            f"1. Run `ollama pull llama3.2:1b` or `ollama pull llama3.1:8b` in your terminal.\n"
                            f"2. Or click **Settings** (gear icon) to switch to **Groq Cloud** (free, instant) or **OpenAI/Claude**."
                        )
                        return

                    if stream_resp.status_code != 200:
                        err_bytes = await stream_resp.aread()
                        yield f"Ollama Error (Status {stream_resp.status_code}): {err_bytes.decode()}"
                        return

                    async for line in stream_resp.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                msg = data.get("message", {})
                                content = msg.get("content", "")
                                if content:
                                    yield content
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"\n[Ollama Connection Error: {str(e)}. Please check if Ollama is running at {self.base_url}]"


    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> str:
        tokens = []
        async for chunk in self.generate_stream(messages, system_prompt, temperature):
            tokens.append(chunk)
        return "".join(tokens)


# -------------------------------------------------------------------------
# Anthropic Client (Claude)
# -------------------------------------------------------------------------

class AnthropicClient(BaseLLMClient):
    """Anthropic Claude Client using official async SDK."""

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(model_name or settings.ANTHROPIC_MODEL)
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = None
        if self.api_key:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Anthropic client: {e}")

    async def is_available(self) -> bool:
        return bool(self.api_key and self._client is not None)

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> AsyncGenerator[str, None]:
        if not self._client:
            yield "Anthropic API key is not configured. Please supply ANTHROPIC_API_KEY in your .env or settings."
            return

        formatted_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages if m["role"] in ["user", "assistant"]
        ]

        try:
            async with self._client.messages.stream(
                model=self.model_name,
                max_tokens=4096,
                temperature=temperature,
                system=system_prompt or "",
                messages=formatted_messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield f"\n[Anthropic API Error: {str(e)}]"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> str:
        tokens = []
        async for chunk in self.generate_stream(messages, system_prompt, temperature):
            tokens.append(chunk)
        return "".join(tokens)


# -------------------------------------------------------------------------
# OpenAI Client (GPT-4o)
# -------------------------------------------------------------------------

class OpenAIClient(BaseLLMClient):
    """OpenAI Client using official async SDK."""

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(model_name or settings.OPENAI_MODEL)
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._client = None
        if self.api_key:
            try:
                import openai
                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")

    async def is_available(self) -> bool:
        return bool(self.api_key and self._client is not None)

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> AsyncGenerator[str, None]:
        if not self._client:
            yield "OpenAI API key is not configured. Please supply OPENAI_API_KEY in your .env or settings."
            return

        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        try:
            stream = await self._client.chat.completions.create(
                model=self.model_name,
                messages=payload_messages,
                temperature=temperature,
                stream=True
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else ""
                if delta:
                    yield delta
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"\n[OpenAI API Error: {str(e)}]"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> str:
        tokens = []
        async for chunk in self.generate_stream(messages, system_prompt, temperature):
            tokens.append(chunk)
        return "".join(tokens)


# -------------------------------------------------------------------------
# Generic OpenAI-Compatible Client (DeepSeek, Groq, OpenRouter, Mistral, Together, vLLM, etc.)
# -------------------------------------------------------------------------

class GenericOpenAICompatibleClient(BaseLLMClient):
    """Universal client for any OpenAI-compatible API endpoint."""

    def __init__(
        self,
        model_name: str,
        base_url: str,
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(model_name)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.custom_headers = custom_headers or {}

    def _get_endpoint_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            **self.custom_headers
        }
        if self.api_key and self.api_key.strip():
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"
        return headers

    async def is_available(self) -> bool:
        # If API key is present or local endpoint
        return bool(self.base_url and (self.api_key or "localhost" in self.base_url or "127.0.0.1" in self.base_url))

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> AsyncGenerator[str, None]:
        url = self._get_endpoint_url()
        headers = self._get_headers()

        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        payload = {
            "model": self.model_name,
            "messages": payload_messages,
            "temperature": temperature,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        logger.error(f"Custom LLM API error ({response.status_code}): {err_text.decode('utf-8', errors='ignore')}")
                        yield f"\n[Custom Model API Error (Status {response.status_code}): {err_text.decode('utf-8', errors='ignore')}]"
                        return

                    async for line in response.aiter_lines():
                        trimmed = line.strip()
                        if not trimmed or trimmed.startswith(":"):
                            continue
                        if trimmed.startswith("data: "):
                            data_str = trimmed[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except Exception:
                                continue
        except Exception as e:
            logger.error(f"Custom LLM connection error: {e}")
            yield f"\n[Connection Error to {self.base_url}: {str(e)}]"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> str:
        tokens = []
        async for chunk in self.generate_stream(messages, system_prompt, temperature):
            tokens.append(chunk)
        return "".join(tokens)


# -------------------------------------------------------------------------
# Dynamic Provider Registry
# -------------------------------------------------------------------------

class ProviderRegistry:
    """Manages active LLM provider selection, runtime keys, custom endpoints, and fallback."""

    def __init__(self):
        self.active_provider_id: str = settings.DEFAULT_LLM_PROVIDER
        self.active_model_name: Optional[str] = None
        self.runtime_anthropic_key: Optional[str] = settings.ANTHROPIC_API_KEY
        self.runtime_openai_key: Optional[str] = settings.OPENAI_API_KEY
        self.custom_providers: Dict[str, Any] = {}

    def register_custom_provider(self, config: Any) -> ProviderInfo:
        """Registers a user-defined custom LLM provider dynamically."""
        provider_id = config.id or f"custom_{re.sub(r'[^a-zA-Z0-9_]', '_', config.name.lower())}_{uuid.uuid4().hex[:6]}"
        config.id = provider_id
        self.custom_providers[provider_id] = config
        logger.info(f"Registered custom provider: {provider_id} ({config.name} - {config.model_name})")

        return ProviderInfo(
            id=provider_id,
            name=f"⚡ {config.name}",
            is_available=True,
            is_active=self.active_provider_id == provider_id,
            current_model=config.model_name,
            available_models=[config.model_name],
            notes=config.notes or f"Custom {config.api_type} model at {config.base_url}"
        )

    def remove_custom_provider(self, provider_id: str) -> bool:
        """Removes a custom provider from the active registry."""
        if provider_id in self.custom_providers:
            del self.custom_providers[provider_id]
            if self.active_provider_id == provider_id:
                self.active_provider_id = "ollama"
                self.active_model_name = None
            logger.info(f"Removed custom provider: {provider_id}")
            return True
        return False

    def get_client(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key_override: Optional[str] = None
    ) -> BaseLLMClient:
        provider = (provider_name or self.active_provider_id).lower()
        model = model_name or self.active_model_name

        # Check if custom provider
        if provider in self.custom_providers:
            cfg = self.custom_providers[provider]
            key = api_key_override or cfg.api_key
            if cfg.api_type == "anthropic_compatible":
                return AnthropicClient(model_name=model or cfg.model_name, api_key=key)
            elif cfg.api_type == "ollama_compatible":
                return OllamaClient(model_name=model or cfg.model_name, base_url=cfg.base_url)
            else:
                return GenericOpenAICompatibleClient(
                    model_name=model or cfg.model_name,
                    base_url=cfg.base_url,
                    api_key=key
                )

        if provider == "anthropic":
            key = api_key_override or self.runtime_anthropic_key
            return AnthropicClient(model_name=model, api_key=key)
        elif provider == "openai":
            key = api_key_override or self.runtime_openai_key
            return OpenAIClient(model_name=model, api_key=key)
        else:
            return OllamaClient(model_name=model)

    async def get_providers_info(self) -> List[ProviderInfo]:
        ollama_cli = self.get_client("ollama")
        anthropic_cli = self.get_client("anthropic")
        openai_cli = self.get_client("openai")

        ollama_ok = await ollama_cli.is_available()
        anthropic_ok = await anthropic_cli.is_available()
        openai_ok = await openai_cli.is_available()

        # Dynamically discover installed Ollama models
        installed_ollama = []
        if isinstance(ollama_cli, OllamaClient):
            installed_ollama = await ollama_cli.get_installed_models()

        default_ollama_models = ["llama3.1:8b", "llama3.2:3b", "qwen2.5:7b", "mistral:7b"]
        ollama_models = list(dict.fromkeys(installed_ollama + default_ollama_models))
        
        # Pick active model for ollama: current user selection > first installed model > default settings model
        if self.active_provider_id == "ollama" and self.active_model_name:
            current_ollama_model = self.active_model_name
        elif installed_ollama:
            current_ollama_model = installed_ollama[0]
        else:
            current_ollama_model = settings.OLLAMA_MODEL

        base_list = [
            ProviderInfo(
                id="ollama",
                name="Ollama (Local)",
                is_available=ollama_ok,
                is_active=self.active_provider_id == "ollama",
                current_model=current_ollama_model,
                available_models=ollama_models,
                notes=f"Local offline models. Found: {', '.join(installed_ollama) if installed_ollama else 'None pulled yet'}."
            ),
            ProviderInfo(
                id="anthropic",
                name="Anthropic Claude",
                is_available=anthropic_ok,
                is_active=self.active_provider_id == "anthropic",
                current_model=(self.active_model_name if self.active_provider_id == "anthropic" else None) or settings.ANTHROPIC_MODEL,
                available_models=["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
                notes="High intelligence cloud reasoning."
            ),

            ProviderInfo(
                id="openai",
                name="OpenAI GPT",
                is_available=openai_ok,
                is_active=self.active_provider_id == "openai",
                current_model=(self.active_model_name if self.active_provider_id == "openai" else None) or settings.OPENAI_MODEL,
                available_models=["gpt-4o", "gpt-4o-mini"],
                notes="Flagship OpenAI cloud models."
            ),
        ]

        # Append all user registered custom providers
        for pid, cfg in self.custom_providers.items():
            base_list.append(
                ProviderInfo(
                    id=pid,
                    name=f"⚡ {cfg.name}",
                    is_available=True,
                    is_active=self.active_provider_id == pid,
                    current_model=cfg.model_name,
                    available_models=[cfg.model_name],
                    notes=cfg.notes or f"{cfg.api_type} at {cfg.base_url}"
                )
            )

        return base_list

    def set_active_provider(
        self,
        provider_id: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.active_provider_id = provider_id
        if model:
            self.active_model_name = model
        if api_key and api_key.strip():
            if provider_id == "anthropic":
                self.runtime_anthropic_key = api_key.strip()
            elif provider_id == "openai":
                self.runtime_openai_key = api_key.strip()
            elif provider_id in self.custom_providers:
                self.custom_providers[provider_id].api_key = api_key.strip()

        logger.info(f"Active provider switched to: {provider_id} (model: {self.active_model_name})")

    async def test_connection(
        self,
        api_type: str,
        base_url: str,
        model_name: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tests live response and latency of a target provider endpoint."""
        start = time.perf_counter()
        try:
            if api_type == "anthropic_compatible":
                client = AnthropicClient(model_name=model_name, api_key=api_key)
            elif api_type == "ollama_compatible":
                client = OllamaClient(model_name=model_name, base_url=base_url)
            else:
                client = GenericOpenAICompatibleClient(
                    model_name=model_name,
                    base_url=base_url,
                    api_key=api_key
                )

            # Send minimal test prompt
            test_messages = [{"role": "user", "content": "Ping test. Reply with 'OK'."}]
            res = await client.generate(test_messages, temperature=0.1)
            latency = (time.perf_counter() - start) * 1000

            if "Error" in res or "error" in res.lower() and len(res) < 100 and "ok" not in res.lower():
                return {
                    "success": False,
                    "latency_ms": round(latency, 1),
                    "message": res.strip(),
                    "sample_output": None
                }

            return {
                "success": True,
                "latency_ms": round(latency, 1),
                "message": f"Successfully connected to {model_name} in {round(latency, 1)}ms!",
                "sample_output": res.strip()[:120]
            }
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {
                "success": False,
                "latency_ms": round(latency, 1),
                "message": f"Connection failed: {str(e)}",
                "sample_output": None
            }


provider_registry = ProviderRegistry()


