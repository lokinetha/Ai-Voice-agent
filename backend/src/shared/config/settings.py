"""
Application Settings & Environment Configuration Bootstrap.

Loads environment variables from project-root .env file using python-dotenv.
Resolves runtime configuration for LLM, STT, TTS, and core services.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from voice.domain.ports.llm_runtime_port import LLMRuntimePort


@lru_cache(maxsize=1)
def find_project_root() -> Path:
    """Find the project root directory containing .env or pyproject.toml.

    Cached for the process lifetime: the result is deterministic for a given
    filesystem layout and this is called on nearly every settings property access.
    """
    current_path = Path(__file__).resolve()
    for parent in [current_path] + list(current_path.parents):
        if (parent / ".env").is_file() or (parent / "pyproject.toml").is_file():
            return parent
    return current_path.parent.parent.parent.parent


def load_env_file() -> bool:
    """Find and load project-root .env file into environment variables."""
    root = find_project_root()
    env_candidate = root / ".env"
    if env_candidate.is_file():
        load_dotenv(dotenv_path=env_candidate, override=False)
        return True
    return False


# Auto-load project-root .env on module import
load_env_file()


class Settings:
    """Central application settings loader resolving environment configuration."""

    def __init__(self) -> None:
        load_env_file()

    @property
    def project_root(self) -> Path:
        return find_project_root()

    def _resolve_path(self, path_str: str) -> str:
        """Resolve path string relative to project_root if not absolute."""
        if not path_str:
            return ""
        path_obj = Path(path_str)
        if not path_obj.is_absolute():
            path_obj = self.project_root / path_obj
        return str(path_obj)

    @property
    def default_language(self) -> str:
        return os.getenv("DEFAULT_LANGUAGE", "en-IN").strip()

    @property
    def supported_languages(self) -> list[str]:
        raw = os.getenv("SUPPORTED_LANGUAGES", "en-IN,te-IN").strip()
        return [lang.strip() for lang in raw.split(",") if lang.strip()]

    @property
    def whisper_language(self) -> str:
        return os.getenv("WHISPER_LANGUAGE", "auto").strip()

    @property
    def gemini_api_key(self) -> str:
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def gemini_model(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    @property
    def llm_provider(self) -> str:
        return os.getenv("LLM_PROVIDER", "gemini").strip().lower()

    @property
    def stt_provider(self) -> str:
        return os.getenv("STT_PROVIDER", "fake").strip().lower()

    @property
    def tts_provider(self) -> str:
        return os.getenv("TTS_PROVIDER", "fake").strip().lower()

    @property
    def whisper_model(self) -> str:
        return os.getenv("WHISPER_MODEL", "large-v3").strip()

    @property
    def whisper_model_path(self) -> str:
        raw = os.getenv("WHISPER_MODEL_PATH", "").strip()
        if not raw:
            default_path = self.project_root / "models" / "faster-whisper-large-v3"
            if default_path.exists():
                return str(default_path)
            return ""
        return self._resolve_path(raw)

    @property
    def whisper_device(self) -> str:
        return os.getenv("WHISPER_DEVICE", "cuda").strip()

    @property
    def whisper_compute_type(self) -> str:
        return os.getenv("WHISPER_COMPUTE_TYPE", "int8_float16").strip()

    @property
    def piper_model_path(self) -> str:
        return self.piper_en_model_path

    @property
    def piper_config_path(self) -> str:
        return self.piper_en_config_path

    @property
    def piper_en_model_path(self) -> str:
        raw = os.getenv("PIPER_EN_MODEL_PATH", "").strip() or os.getenv("PIPER_MODEL_PATH", "").strip()
        if not raw:
            default_path = self.project_root / "models" / "en_US-lessac-medium.onnx"
            if default_path.is_file():
                return str(default_path)
            return ""
        return self._resolve_path(raw)

    @property
    def piper_en_config_path(self) -> str:
        raw = os.getenv("PIPER_EN_CONFIG_PATH", "").strip() or os.getenv("PIPER_CONFIG_PATH", "").strip()
        if not raw:
            if self.piper_en_model_path:
                candidate = Path(f"{self.piper_en_model_path}.json")
                if candidate.is_file():
                    return str(candidate)
            return ""
        return self._resolve_path(raw)

    @property
    def piper_te_model_path(self) -> str:
        raw = os.getenv("PIPER_TE_MODEL_PATH", "").strip()
        if not raw:
            return ""
        return self._resolve_path(raw)

    @property
    def piper_te_config_path(self) -> str:
        raw = os.getenv("PIPER_TE_CONFIG_PATH", "").strip()
        if not raw:
            if self.piper_te_model_path:
                candidate = Path(f"{self.piper_te_model_path}.json")
                if candidate.is_file():
                    return str(candidate)
            return ""
        return self._resolve_path(raw)

    @property
    def piper_device(self) -> str:
        return os.getenv("PIPER_DEVICE", "cpu").strip()

    @property
    def piper_length_scale(self) -> float:
        val = os.getenv("PIPER_LENGTH_SCALE", "1.0").strip()
        try:
            return float(val)
        except ValueError:
            return 1.0

    @property
    def piper_noise_scale(self) -> float:
        val = os.getenv("PIPER_NOISE_SCALE", "0.667").strip()
        try:
            return float(val)
        except ValueError:
            return 0.667

    @property
    def piper_noise_w_scale(self) -> float:
        val = os.getenv("PIPER_NOISE_W_SCALE", "0.8").strip()
        try:
            return float(val)
        except ValueError:
            return 0.8

    def is_gemini_api_key_valid(self) -> bool:
        """Check if GEMINI_API_KEY is configured and not a placeholder."""
        key = self.gemini_api_key
        return bool(key and key != "YOUR_GEMINI_API_KEY")

    def get_masked_api_key(self) -> str:
        """Return masked API key for safe debugging without exposing secrets."""
        key = self.gemini_api_key
        if key and len(key) > 6 and key != "YOUR_GEMINI_API_KEY":
            return f"***{key[-4:]}"
        return "***"


# Global singleton settings instance
settings = Settings()


def resolve_llm_adapter(cfg: Settings = settings) -> LLMRuntimePort:
    """Resolve configured LLMRuntimePort adapter based on Settings configuration."""
    provider = cfg.llm_provider
    if provider in ("fake", "mock"):
        from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
            FakeLLMRuntimeAdapter,
        )

        return FakeLLMRuntimeAdapter()

    if provider == "gemini":
        if not cfg.is_gemini_api_key_valid():
            raise ValueError(
                "GEMINI_API_KEY is missing or unconfigured in Settings configuration. "
                "Please set a valid GEMINI_API_KEY in your .env file or environment when LLM_PROVIDER=gemini."
            )
        from voice.infrastructure.adapters.gemini_llm_adapter import (
            GeminiLLMAdapter,
        )

        return GeminiLLMAdapter(
            api_key=cfg.gemini_api_key,
            model_name=cfg.gemini_model,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER configuration: '{provider}'")
