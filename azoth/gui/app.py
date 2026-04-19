"""Azoth main window — frame navigation + model loading."""

import threading
import customtkinter as ctk
from azoth.gui import theme as T
from azoth.gui.home_frame import HomeFrame
from azoth.gui.transcription_frame import TranscriptionFrame
from azoth.gui.history_frame import HistoryFrame

from azoth.core.audio import AudioCapture
from azoth.core.transcription import TranscriptionEngine
from azoth.core.database import TranscriptionDB
from azoth.core.analysis import AnalysisEngine


class AzothApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Window setup ─────────────────────────────────────────────
        self.title("✦ AZOTH — Som em Texto")
        self.geometry("960x680")
        self.minsize(860, 580)
        self.configure(fg_color=T.BG_DARK)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ── Core services ────────────────────────────────────────────
        self.audio = AudioCapture()
        self.engine = TranscriptionEngine()
        self.db = TranscriptionDB()
        self.analysis = AnalysisEngine()

        # ── Container ────────────────────────────────────────────────
        self.container = ctk.CTkFrame(self, fg_color=T.BG_DARK)
        self.container.pack(fill="both", expand=True)

        # ── Frames ───────────────────────────────────────────────────
        self.frames = {}
        self._current_frame = None

        self.frames["home"] = HomeFrame(self.container, self)
        self.frames["transcription"] = TranscriptionFrame(self.container, self)
        self.frames["history"] = HistoryFrame(self.container, self)

        self.show_frame("home")

        # ── Load model in background ─────────────────────────────────
        self.frames["home"].set_status("⏳ Carregando modelo Whisper...")
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        def on_status(msg):
            self.after(0, lambda: self.frames["home"].set_status(msg))

        self.engine.load_model(on_status=on_status)
        self.after(0, lambda: self.frames["home"].set_status(
            f"✓ Whisper {self.engine.model_name} carregado no {self.engine.device.upper()}"
        ))

    def show_frame(self, name, **kwargs):
        """Navigate to a frame by name."""
        if self._current_frame:
            self._current_frame.pack_forget()

        frame = self.frames[name]
        frame.pack(in_=self.container, fill="both", expand=True)

        if hasattr(frame, "on_show"):
            frame.on_show(**kwargs)

        self._current_frame = frame
