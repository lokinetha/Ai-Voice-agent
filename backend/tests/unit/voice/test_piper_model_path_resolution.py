"""
Unit and regression tests verifying Piper model path configuration flow.

Proves:
- Empty CLI model argument falls back to Settings.piper_model_path.
- Relative paths resolve relative to project root, not current working directory.
- Resolved path exists on disk before Piper initialization.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from shared.config.settings import settings
from voice.infrastructure.adapters.piper_tts_adapter import PiperTTSAdapter


class TestPiperModelPathResolution(unittest.TestCase):
    """Unit test suite verifying Piper model path resolution."""

    def test_empty_cli_model_argument_falls_back_to_settings(self) -> None:
        """Verify empty CLI string fallback to settings.piper_model_path."""
        adapter = PiperTTSAdapter(model_path="", config_path="")
        self.assertEqual(adapter.model_path, settings.piper_model_path)
        self.assertEqual(adapter.config_path, settings.piper_config_path)

    def test_relative_model_path_resolves_to_project_root(self) -> None:
        """Verify relative paths resolve relative to project_root."""
        adapter = PiperTTSAdapter(model_path="models/en_US-lessac-medium.onnx")
        expected = str(settings.project_root / "models" / "en_US-lessac-medium.onnx")
        self.assertEqual(adapter.model_path, expected)

    def test_resolved_model_path_exists_on_disk(self) -> None:
        """Verify that resolved model path exists before Piper initialization."""
        adapter = PiperTTSAdapter()
        if adapter.model_path:
            self.assertTrue(
                os.path.exists(adapter.model_path),
                f"Resolved model path does not exist: '{adapter.model_path}'",
            )
            self.assertTrue(Path(adapter.model_path).is_absolute())


if __name__ == "__main__":
    unittest.main()
