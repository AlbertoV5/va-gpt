from app.system.logger import log_json
from app.types import EmbeddingData
from openai import Embedding


class Embedder:
    """
    A class to interact with the OpenAI Embeddings API.
    """

    def __init__(self, model: str = "text-embedding-ada-002") -> None:
        self.model = model

    async def get(self, text: str) -> list[float] | None:
        """
        Sends a request to the OpenAI Embeddings API.
        """
        try:
            # get the first item of the response data
            response = await Embedding.acreate(input=text, model=self.model)
            embedding: EmbeddingData = response["data"][0]
            return embedding["embedding"]
        except BaseException as e:
            log_json({"error": f"Failed to get embedding: {e}"})
