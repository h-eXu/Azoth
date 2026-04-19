"""Whisper transcription engine — GPU-aware with timing."""

import time
import whisper
import torch


class TranscriptionEngine:
    def __init__(self, model_name="large-v3-turbo"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None

    def load_model(self, on_status=None):
        """Load Whisper model. Calls on_status(msg) for progress updates."""
        if on_status:
            on_status(f"Carregando Whisper ({self.model_name}) no {self.device.upper()}...")
        self.model = whisper.load_model(self.model_name, device=self.device)
        if on_status:
            on_status(f"Modelo carregado no {self.device.upper()} ✓")

    def transcribe(self, audio_path, language="pt"):
        """Transcribe audio file. Returns (text, elapsed_seconds)."""
        start = time.time()
        result = self.model.transcribe(
            audio_path, language=language, verbose=False, fp16=False
        )
        elapsed = time.time() - start
        text = result["text"].strip()
        return text, elapsed
