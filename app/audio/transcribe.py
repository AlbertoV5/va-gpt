from torchaudio.transforms import Resample
from torch import Tensor, float32, dtype
from whisper import load_model

from app.system.config import TranscribeConfig


__all__ = ["Transcribe"]


class Transcribe:
    """Use Whisper for STT"""

    def __init__(
        self,
        config: TranscribeConfig,
        samplerate: int = 24000,
        model_samplerate: int = 16000,
        model_dtype: dtype = float32,
    ) -> None:
        """Load ASR model for speech to text and setup transform values."""
        self.config = config
        # audio
        self.samplerate = samplerate
        self.model_dtype = model_dtype
        self.model_samplerate = model_samplerate
        # ml
        self.model = load_model(self.config.model)
        self.resample = Resample(samplerate, model_samplerate, dtype=model_dtype)

    def update_initial_prompt(self, text: str):
        """Add given text to start of initial prompt, comma separated."""
        self.config.initial_prompt = f"{text}, {self.config.initial_prompt}"

    def transform(self, X: Tensor):
        """Convert tensor to model compatible form."""
        if X.dtype != self.model_dtype:
            X = X.type(self.model_dtype)
        if self.samplerate != self.model_samplerate:
            return self.resample(X)
        return X

    def predict(self, X: Tensor, no_speech_threshold: float = 0.6) -> str:
        """Transcribe speech to text using torch Tensor data."""
        y_pred = self.model.transcribe(
            self.transform(X),
            fp16=self.config.fp16,
            language=self.config.language,
            initial_prompt=self.config.initial_prompt,
            no_speech_threshold=no_speech_threshold,
        )
        return y_pred["text"].strip()
