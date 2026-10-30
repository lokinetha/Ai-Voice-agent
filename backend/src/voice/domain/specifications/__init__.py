"""
Voice Domain Specifications package init.
"""

from voice.domain.specifications.active_voice_session_spec import (
    ActiveVoiceSessionSpec,
)
from voice.domain.specifications.can_accept_audio_spec import (
    CanAcceptAudioSpec,
)

__all__ = [
    "ActiveVoiceSessionSpec",
    "CanAcceptAudioSpec",
]
