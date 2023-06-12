from torch import Tensor, cat, zeros
from torchaudio import load, save
from typing import BinaryIO

from app.system.config import AudioConfig
from app.system.logger import log_json


class Recorder:
    def __init__(
        self,
        config: AudioConfig,
        channels: int = 1,
        padding_seconds: float = 0.5,
    ) -> None:
        """Initialize recorder with audio config and a padding in seconds for audio files."""
        # internal tape state
        self.tape: Tensor | None = None
        # config
        self.n_channels = channels
        self.samplerate = config.channel.samplerate
        self.dtype = config.channel.dtype
        self.ceiling = config.channel.fullscale
        # silence padding in between files
        self.silence = zeros(
            self.n_channels,
            int(self.samplerate * padding_seconds),
            dtype=self.dtype,
        )

    def to_tape(self, file: BinaryIO):
        """Load ogg file into Tensor and append to internal tape."""
        try:
            tensor, sr = load(file, format="ogg")
            assert sr == self.samplerate
            if self.tape is None:
                self.tape = tensor
            else:
                self.tape = cat([self.tape, self.silence, tensor], dim=1)
        except BaseException as e:
            log_json({"error": f"Could not read ogg file to tape: {e}"})
            return None

    def save_tape(self, filepath: str):
        """Record internal tape to filepath and set it to None."""
        try:
            save(filepath, self.tape, sample_rate=self.samplerate)
            self.tape = None
        except BaseException as e:
            print(f"Could not save tensor as file {e}")
            return None
        return filepath

    def save(self, X: Tensor, filepath: str):
        """Convert Tensor to audio file. Using torchaudio.save.
        Format not specified (uses file extension).
        https://pytorch.org/audio/stable/backend.html

        Args:
            X (Tensor): Tensor.
            filepath (str): Filepath.
        """
        try:
            save(
                filepath,
                (X * self.ceiling).type(self.dtype).reshape((1, -1)),
                sample_rate=self.samplerate,
            )
        except BaseException as e:
            print(f"Could not save tensor as file {e}")
            return None
        return filepath
