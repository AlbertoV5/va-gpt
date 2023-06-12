from tempfile import TemporaryFile
from typing import BinaryIO
from boto3 import client

from app.speech.polly import PollyClient
from app.speech.voice import VoiceStyle
from app.system.logger import log_json


class Speech:
    def __init__(
        self,
        voice: VoiceStyle,
        samplerate: int,
        polly: PollyClient = None,
    ) -> None:
        """Setup client and config for speech synthesis.

        Args:
            voice (VoiceStyle): Voice style.
            sr (int): Sample Rate.
            polly (PollyClient, optional): AWS SDK Client. Defaults to None.
        """
        self.voice = voice
        self.samplerate = samplerate
        self.client = polly if polly else client("polly")

    def synthesize(self, text: str, use_ssml: bool = True, as_file: bool = True) -> BinaryIO:
        """AWS Polly Voice Synthesis with SSML. Store to temp file if as_file, else AudioStream from response.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/polly/client/synthesize_speech.html
        """
        text = self.sanitize(text)
        if not text:
            return log_json({"error": "Text to synthesize is empty."})
        try:
            request = {
                "Text": self.voice.ssml.format(text=text) if use_ssml else text,
                "TextType": "ssml" if use_ssml else "text",
                "LanguageCode": self.voice.language,
                "SampleRate": str(self.samplerate),
                "VoiceId": self.voice.voice_id,
                "OutputFormat": "ogg_vorbis",
                "Engine": self.voice.engine,
            }
            response = self.client.synthesize_speech(**request)
            if as_file:
                file = TemporaryFile("w+b")
                file.write(response["AudioStream"].read())
                file.seek(0)
                return file
            return response["AudioStream"]
        except BaseException as e:
            log_json({"request": request, "exception": str(e)})

    def sanitize(self, text: str):
        """Prepare string for speech request. Remove code strings."""
        s = "".join(x for i, x in enumerate(text.split("```")) if i % 2 == 0)
        return s.replace("<", "").replace(">", "")
