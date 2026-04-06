"""Whisper transcriber using faster-whisper with KB-Whisper models."""

import os
import sys

# Add NVIDIA pip package DLL paths so CTranslate2 can find cublas/cudnn.
# Handles both normal Python environments and PyInstaller bundles.
def _add_nvidia_dll_dirs():
    candidates = []

    if getattr(sys, "frozen", False):
        # PyInstaller onedir: DLLs land next to the exe or in _internal/
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(exe_dir)
        if hasattr(sys, "_MEIPASS"):
            candidates.append(sys._MEIPASS)
        for sub in ("nvidia/cublas/bin", "nvidia/cudnn/bin"):
            candidates.append(os.path.join(exe_dir, sub))
            if hasattr(sys, "_MEIPASS"):
                candidates.append(os.path.join(sys._MEIPASS, sub))
    else:
        # Normal venv: packages are in site-packages/nvidia/...
        site_pkgs = os.path.join(os.path.dirname(sys.executable), "..", "lib", "site-packages")
        for sub in ("nvidia/cublas/bin", "nvidia/cudnn/bin"):
            candidates.append(os.path.normpath(os.path.join(site_pkgs, sub)))

    for path in candidates:
        if os.path.isdir(path):
            os.add_dll_directory(path)
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")

_add_nvidia_dll_dirs()

import numpy as np
from faster_whisper import WhisperModel

import config
from config import WHISPER_MODEL, LANGUAGE


class Transcriber:
    def __init__(self, model_name=WHISPER_MODEL, language=LANGUAGE):
        self.model_name = model_name
        self.language = language
        self._model = None

    def load_model(self):
        """Load the Whisper model. Call once at startup."""
        print(f"[transcriber] Laddar modell {self.model_name} ...")
        try:
            model = WhisperModel(
                self.model_name,
                device="cuda",
                compute_type="float16",
            )
            # Verify CUDA actually works by running a tiny transcription
            dummy = np.zeros(16000, dtype=np.float32)
            segments, _ = model.transcribe(dummy)
            for _ in segments:
                pass
            self._model = model
            print("[transcriber] Modell laddad (CUDA)!")
        except (RuntimeError, Exception) as e:
            print(f"[transcriber] CUDA ej tillgänglig ({e}), faller tillbaka på CPU...")
            self._model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
            )
            print("[transcriber] Modell laddad (CPU)!")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a float32 audio array and return the full text."""
        if self._model is None:
            raise RuntimeError("Model not loaded — call load_model() first")

        if len(audio) == 0:
            return ""

        segments, info = self._model.transcribe(
            audio,
            language=self.language,
            beam_size=config.get("beam_size") or 1,
            word_timestamps=True,
            vad_filter=True,
        )

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        return " ".join(text_parts)

    def transcribe_streaming(self, audio: np.ndarray):
        """Yield segments one by one for progressive display."""
        if self._model is None:
            raise RuntimeError("Model not loaded — call load_model() first")

        if len(audio) == 0:
            return

        segments, info = self._model.transcribe(
            audio,
            language=self.language,
            beam_size=config.get("beam_size") or 1,
            word_timestamps=True,
            vad_filter=True,
        )

        for segment in segments:
            yield segment
