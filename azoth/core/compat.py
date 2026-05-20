"""
azoth/core/compat.py
====================
Patches de compatibilidade aplicados no nível de importação.
Deve ser o PRIMEIRO import em qualquer módulo que use pyannote-audio.

Patches aplicados:
  1. torchaudio.AudioMetaData / info() / list_audio_backends()  — torchaudio 2.9+ removeu do namespace raiz
  2. torchaudio.load()                                           — redireciona para soundfile (evita torchcodec)
  3. huggingface_hub.hf_hub_download                            — traduz use_auth_token → token (hf_hub 1.x)
  4. torch.load                                                  — weights_only=False por padrão (PyTorch 2.6)
  5. lightning_fabric.utilities.cloud_io._load                  — força weights_only=False
  6. speechbrain LazyModule                                      — dunder attrs levantam AttributeError (evita ImportError do k2)
"""

# ── Patch 1: torchaudio — AudioMetaData / info() / list_audio_backends() ──
import torchaudio as _torchaudio

if not hasattr(_torchaudio, "AudioMetaData"):
    import soundfile as _sf
    from dataclasses import dataclass

    @dataclass
    class AudioMetaData:
        sample_rate: int
        num_frames: int
        num_channels: int
        bits_per_sample: int = 16
        encoding: str = "PCM_S"

    def _info(filepath, *args, **kwargs):
        info = _sf.info(filepath)
        return AudioMetaData(
            sample_rate=info.samplerate,
            num_frames=info.frames,
            num_channels=info.channels,
        )

    def _list_audio_backends():
        return ["soundfile"]

    _torchaudio.AudioMetaData = AudioMetaData
    _torchaudio.info = _info
    _torchaudio.list_audio_backends = _list_audio_backends


# ── Patch 2: torchaudio.load() — redireciona para soundfile ───────────────
import torch as _torch
import numpy as _np

if not hasattr(_torchaudio, "_azoth_load_patched"):
    import soundfile as _sf

    def _patched_torchaudio_load(filepath, frame_offset=0, num_frames=-1, *args, **kwargs):
        data, samplerate = _sf.read(
            filepath,
            start=frame_offset,
            stop=None if num_frames == -1 else frame_offset + num_frames,
            dtype="float32",
            always_2d=True,
        )
        tensor = _torch.from_numpy(_np.ascontiguousarray(data.T))  # (channels, samples)
        return tensor, samplerate

    _torchaudio.load = _patched_torchaudio_load
    _torchaudio._azoth_load_patched = True


# ── Patch 3: huggingface_hub — use_auth_token → token ─────────────────────
import huggingface_hub as _hf_hub
from huggingface_hub import hf_hub_download as _orig_hf_hub_download

def _patched_hf_hub_download(*args, **kwargs):
    if "use_auth_token" in kwargs:
        kwargs["token"] = kwargs.pop("use_auth_token")
    return _orig_hf_hub_download(*args, **kwargs)

_hf_hub.hf_hub_download = _patched_hf_hub_download

import huggingface_hub.file_download as _hf_file_download
_hf_file_download.hf_hub_download = _patched_hf_hub_download


# ── Patch 4: torch.load — weights_only=False por padrão ───────────────────
if not getattr(_torch, "_azoth_load_patched", False):
    _orig_load = _torch.load

    def _patched_load(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return _orig_load(*args, **kwargs)

    _torch.load = _patched_load
    _torch._azoth_load_patched = True


# ── Patch 5: lightning_fabric._load — força weights_only=False ────────────
try:
    import lightning_fabric.utilities.cloud_io as _cloud_io

    def _patched_pl_load(path, map_location=None, **kwargs):
        kwargs["weights_only"] = False
        return _torch.load(path, map_location=map_location, **kwargs)

    _cloud_io._load = _patched_pl_load
except Exception:
    pass


# ── Patch 6: speechbrain LazyModule — dunder attrs não forçam import ───────
try:
    import speechbrain.utils.importutils as _sb_importutils

    _OrigLazy = _sb_importutils.LazyModule
    _orig_lazy_getattr = _OrigLazy.__getattr__

    def _safe_lazy_getattr(self, attr: str):
        if attr.startswith("__") and attr.endswith("__"):
            raise AttributeError(attr)
        return _orig_lazy_getattr(self, attr)

    _OrigLazy.__getattr__ = _safe_lazy_getattr

except Exception:
    pass