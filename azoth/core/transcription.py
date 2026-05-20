"""Whisper transcription engine — GPU-aware with lazy load/unload."""

import time


class TranscriptionEngine:
    def __init__(self, model_name="small"):
        import torch

        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None

    def load_model(self, on_status=None):
        """Load Whisper model. Calls on_status(msg) for progress updates.
        Safe to call multiple times — skips if already loaded."""
        if self.model is not None:
            return

        import whisper

        if on_status:
            on_status(f"Carregando Whisper ({self.model_name}) no {self.device.upper()}...")
        self.model = whisper.load_model(self.model_name, device=self.device)
        if on_status:
            on_status(f"Modelo carregado no {self.device.upper()} ✓")

    def transcribe(self, audio_path, language="pt", on_status=None):
        """Transcribe audio file. Returns (text, segments, elapsed_seconds).
        Loads the model automatically if not already loaded."""
        if self.model is None:
            self.load_model(on_status=on_status)

        start = time.time()
        # fp16=False: a GTX 1650 não tem Tensor Cores e produz NaN com fp16
        result = self.model.transcribe(
            audio_path, language=language, verbose=False, fp16=False
        )
        elapsed = time.time() - start
        text = result["text"].strip()
        segments = result["segments"]
        return text, segments, elapsed

    def unload_model(self):
        """Libera VRAM após transcrição."""
        if self.model is None:
            return
        import gc
        import torch

        # Move o modelo para CPU antes de deletar (libera VRAM de forma confiável)
        try:
            self.model.cpu()
        except Exception:
            pass

        self.model = None
        if self.device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()