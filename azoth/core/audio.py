"""
Audio capture layer — separated for future meeting detection integration.
Supports: microphone, system audio (VB-Cable), local files, YouTube.
"""

import os
import tempfile
import uuid
import subprocess
import threading

import sounddevice as sd
import soundfile as sf
import numpy as np
from pytubefix import YouTube

SAMPLE_RATE = 48000


class AudioCapture:
    """Thread-safe audio recorder with start/stop control."""

    def __init__(self, sample_rate=SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._recording = False
        self._frames = []
        self._thread = None
        self._stop_event = threading.Event()

    # ── Device listing ────────────────────────────────────────────────

    @staticmethod
    def list_input_devices():
        """Return list of (index, name) for input-capable devices."""
        devices = sd.query_devices()
        return [
            (i, d["name"])
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]

    # ── Recording ─────────────────────────────────────────────────────

    def start_recording(self, device=None):
        """Start recording in a background thread."""
        self._frames = []
        self._stop_event.clear()
        self._recording = True
        self._thread = threading.Thread(
            target=self._record_loop, args=(device,), daemon=True
        )
        self._thread.start()

    def _record_loop(self, device):
        try:
            with sd.InputStream(
                samplerate=self.sample_rate, channels=1, device=device
            ) as stream:
                while not self._stop_event.is_set():
                    data, _ = stream.read(1024)
                    self._frames.append(data)
        except Exception:
            pass
        finally:
            self._recording = False

    def stop_recording(self):
        """Stop recording and return path to the WAV file."""
        self._stop_event.set()
        self._recording = False
        if self._thread:
            self._thread.join(timeout=3)
        filepath = tempfile.mktemp(suffix=".wav")
        if self._frames:
            sf.write(filepath, np.vstack(self._frames), self.sample_rate)
        return filepath

    @property
    def is_recording(self):
        return self._recording

    # ── File import ───────────────────────────────────────────────────

    @staticmethod
    def import_file(filepath):
        """Import audio/video file; converts non-WAV to WAV via ffmpeg."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        ext = os.path.splitext(filepath)[1].lower()
        name = os.path.basename(filepath)
        if ext in [".mp4", ".m4a", ".mp3", ".ogg"]:
            output = tempfile.mktemp(suffix=".wav")
            subprocess.run(
                ["ffmpeg", "-i", filepath, "-ac", "1", "-ar", "48000", "-y", output],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return output, name
        return filepath, name

    # ── YouTube ───────────────────────────────────────────────────────

    @staticmethod
    def download_youtube(url):
        """Download audio from YouTube video, return (filepath, title)."""
        yt = YouTube(url)
        filename = f"{uuid.uuid4()}.wav"
        yt.streams.filter(only_audio=True).first().download(filename=filename)
        return filename, yt.title
