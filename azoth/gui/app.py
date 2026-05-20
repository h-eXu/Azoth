"""Azoth main window — frame navigation + model loading."""

import threading
import customtkinter as ctk
from azoth.gui import theme as T
from azoth.gui.home_frame import HomeFrame
from azoth.gui.transcription_frame import TranscriptionFrame
from azoth.gui.history_frame import HistoryFrame


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

        # ── Core services (loaded in background) ─────────────────────
        self.audio = None
        self.engine = None
        self.db = None
        self.analysis = None

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

        # ── Load services in background after window is visible ──────
        self.frames["home"].set_status("⏳ Inicializando...")
        self.after(50, self._start_background_init)

    def _start_background_init(self):
        """Kick off service loading in a background thread."""
        threading.Thread(target=self._load_services, daemon=True).start()

    def _load_services(self):
        """Import heavy modules and initialize services off the main thread."""
        def status(msg):
            self.after(0, lambda: self.frames["home"].set_status(msg))

        # ── Import core modules (the heavy part) ─────────────────────
        status("⏳ Carregando módulos...")
        from azoth.core.audio import AudioCapture
        from azoth.core.transcription import TranscriptionEngine
        from azoth.core.database import TranscriptionDB
        from azoth.core.analysis import AnalysisEngine

        # ── Instantiate services ─────────────────────────────────────
        self.audio = AudioCapture()
        self.db = TranscriptionDB()
        self.analysis = AnalysisEngine()
        self.engine = TranscriptionEngine()

        # Whisper carrega sob demanda (na hora de transcrever) para economizar VRAM
        status(
            f"✓ Pronto — Whisper {self.engine.model_name} será carregado sob demanda "
            f"({self.engine.device.upper()})"
        )

    def show_frame(self, name, **kwargs):
        """Navigate to a frame by name."""
        if self._current_frame:
            self._current_frame.pack_forget()

        frame = self.frames[name]
        frame.pack(in_=self.container, fill="both", expand=True)

        if hasattr(frame, "on_show"):
            frame.on_show(**kwargs)

        self._current_frame = frame

