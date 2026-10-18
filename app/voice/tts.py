"""Text-To-Speech (TTS) engine using Windows Native Speech Synthesis."""
from __future__ import annotations

import subprocess
from app.core.config import logger


class WindowsNativeTTS:
    """Uses Windows built-in System.Speech.Synthesis for 100% offline local TTS."""

    def __init__(self, rate: int = 1, volume: int = 100):
        self.rate = rate
        self.volume = volume

    def speak(self, text: str) -> bool:
        """Speak the text through Windows audio device."""
        if not text.strip():
            return False

        # Sanitize text for powershell string
        sanitized = text.replace('"', '""').replace("'", "''").replace("`", "")[:500]

        ps_script = f"""
        Add-Type -AssemblyName System.Speech
        $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
        $synth.Rate = {self.rate}
        $synth.Volume = {self.volume}
        $synth.Speak("{sanitized}")
        """

        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                check=True,
                capture_output=True,
                timeout=20,
            )
            return True
        except Exception as e:
            logger.error(f"Erro na síntese de voz nativa: {e}")
            return False
