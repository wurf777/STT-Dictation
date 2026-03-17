"""Audio recorder using sounddevice — captures microphone input as a numpy array."""

import numpy as np
import sounddevice as sd
import threading

from config import SAMPLE_RATE


def _trim_silence(audio, threshold=0.01, margin=1600):
    """Trim leading and trailing silence from audio.

    Args:
        threshold: amplitude below this is considered silence
        margin: samples to keep before/after speech (100ms at 16kHz)
    """
    if len(audio) == 0:
        return audio

    above = np.abs(audio) > threshold
    if not np.any(above):
        return np.array([], dtype="float32")

    indices = np.where(above)[0]
    start = max(0, indices[0] - margin)
    end = min(len(audio), indices[-1] + margin)
    return audio[start:end]


class Recorder:
    def __init__(self, sample_rate=SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._frames = []
        self._stream = None
        self._lock = threading.Lock()

    def start(self, device=None):
        """Start recording from the specified (or default) microphone."""
        with self._lock:
            self._frames = []
            try:
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    device=device,
                    callback=self._audio_callback,
                )
                self._stream.start()
            except sd.PortAudioError as e:
                print(f"[recorder] Kunde inte starta mikrofon: {e}")
                self._stream = None

    def stop(self) -> np.ndarray:
        """Stop recording and return the captured audio as a 1-D float32 numpy array."""
        with self._lock:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            if not self._frames:
                return np.array([], dtype="float32")

            audio = np.concatenate(self._frames, axis=0).flatten()
            self._frames = []
            return _trim_silence(audio)

    @property
    def is_recording(self) -> bool:
        return self._stream is not None and self._stream.active

    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio block."""
        if status:
            print(f"[recorder] {status}")
        self._frames.append(indata.copy())
