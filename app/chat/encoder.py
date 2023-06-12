"""
This exists mostly for testing purposes.
"""
from tiktoken import encoding_for_model


class Encoder:
    def __init__(self, model: str) -> None:
        self.encoding = encoding_for_model(model)

    def count(self, text: str) -> int:
        """Encode entire string into list of tokens, return length."""
        return len(self.encoding.encode(text) if text else [])

    def encode_bias(self, data: dict[str, float]) -> dict[int, float]:
        """Convert strings in bias to tokens ids."""
        return {
            token: weight for text, weight in data.items() for token in self.encoding.encode(text)
        }
