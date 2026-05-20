"""Speaker diarization engine using pyannote-audio."""

import azoth.core.compat

import torch


def load_pipeline(hf_token: str):
    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
    )
    if torch.cuda.is_available():
        pipeline = pipeline.to(torch.device("cuda"))
    return pipeline


def diarize(audio_path: str, hf_token: str) -> list[dict]:
    """Retorna [{"speaker": "SPEAKER_00", "start": 0.0, "end": 3.5}, ...]"""
    pipeline = load_pipeline(hf_token)
    diarization = pipeline(audio_path)
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({"speaker": speaker, "start": turn.start, "end": turn.end})
        
    import gc
    del pipeline
    del diarization
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
    
    return segments


def merge(whisper_segments: list[dict], diarization_segments: list[dict]) -> str:
    """
    Alinha segmentos do Whisper com falantes do pyannote.
    Se só 1 falante detectado, retorna texto simples sem labels.
    Se 2+ falantes, retorna 'SPEAKER_00: texto' por linha.
    """
    speakers = {d["speaker"] for d in diarization_segments}

    lines = []
    for w in whisper_segments:
        mid = (w["start"] + w["end"]) / 2
        speaker = None
        for d in diarization_segments:
            if d["start"] <= mid <= d["end"]:
                speaker = d["speaker"]
                break

        if len(speakers) <= 1:
            lines.append(w["text"].strip())
        else:
            label = speaker if speaker else "DESCONHECIDO"
            lines.append(f"{label}: {w['text'].strip()}")

    separator = " " if len(speakers) <= 1 else "\n"
    return separator.join(lines)