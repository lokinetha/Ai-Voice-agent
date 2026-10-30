"""
Unit tests for Settings environment variable loader.

Verifies loading from project-root .env file and environment overrides for:
GEMINI_API_KEY, GEMINI_MODEL, LLM_PROVIDER, STT_PROVIDER, TTS_PROVIDER,
WHISPER_MODEL, and WHISPER_DEVICE.

Uses safe dummy environment values without exposing or logging real secrets.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from shared.config.settings import Settings, load_env_file


class TestSettings(unittest.TestCase):
    """Unit test suite for Settings configuration loader."""

    def test_load_env_file_resolves_project_root_env(self) -> None:
        """Verify load_env_file successfully finds and loads the root .env file."""
        loaded = load_env_file()
        self.assertTrue(loaded)

    def test_settings_resolves_all_configuration_variables(self) -> None:
        """Verify resolution of required environment variables from Settings."""
        settings = Settings()

        self.assertIsNotNone(settings.gemini_api_key)
        self.assertTrue(len(settings.gemini_model) > 0)
        self.assertTrue(len(settings.llm_provider) > 0)
        self.assertTrue(len(settings.stt_provider) > 0)
        self.assertTrue(len(settings.tts_provider) > 0)
        self.assertTrue(len(settings.whisper_model) > 0)
        self.assertTrue(len(settings.whisper_device) > 0)

    def test_settings_environment_override_with_safe_dummy_values(self) -> None:
        """Verify settings resolution with explicit safe dummy environment variables."""
        dummy_model_path = str(Path(__file__).resolve())
        dummy_config_path = str(Path(__file__).resolve()) + ".json"

        dummy_env = {
            "GEMINI_API_KEY": "dummy_safe_key_999999",
            "GEMINI_MODEL": "dummy-gemini-model-v1",
            "LLM_PROVIDER": "dummy_llm",
            "STT_PROVIDER": "dummy_stt",
            "TTS_PROVIDER": "dummy_tts",
            "WHISPER_MODEL": "small",
            "WHISPER_DEVICE": "cuda",
            "PIPER_EN_MODEL_PATH": dummy_model_path,
            "PIPER_EN_CONFIG_PATH": dummy_config_path,
            "PIPER_TE_MODEL_PATH": dummy_model_path,
            "PIPER_TE_CONFIG_PATH": dummy_config_path,
            "PIPER_DEVICE": "cpu",
            "PIPER_LENGTH_SCALE": "1.2",
            "PIPER_NOISE_SCALE": "0.5",
            "PIPER_NOISE_W_SCALE": "0.7",
        }

        with patch.dict(os.environ, dummy_env):
            s = Settings()

            # Verify dummy environment variable resolution
            self.assertEqual(s.gemini_api_key, "dummy_safe_key_999999")
            self.assertEqual(s.gemini_model, "dummy-gemini-model-v1")
            self.assertEqual(s.llm_provider, "dummy_llm")
            self.assertEqual(s.stt_provider, "dummy_stt")
            self.assertEqual(s.tts_provider, "dummy_tts")
            self.assertEqual(s.whisper_model, "small")
            self.assertEqual(s.whisper_device, "cuda")
            self.assertEqual(s.piper_en_model_path, dummy_model_path)
            self.assertEqual(s.piper_en_config_path, dummy_config_path)
            self.assertEqual(s.piper_te_model_path, dummy_model_path)
            self.assertEqual(s.piper_te_config_path, dummy_config_path)
            self.assertEqual(s.piper_device, "cpu")
            self.assertEqual(s.piper_length_scale, 1.2)
            self.assertEqual(s.piper_noise_scale, 0.5)
            self.assertEqual(s.piper_noise_w_scale, 0.7)

            # Verify safe secret masking
            masked_key = s.get_masked_api_key()
            self.assertNotIn("dummy_safe_key_999999", masked_key)
            self.assertEqual(masked_key, "***9999")


if __name__ == "__main__":
    unittest.main()
