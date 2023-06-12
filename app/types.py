from typing import (
    TypeAlias,
    NamedTuple,
    BinaryIO,
    TypedDict,
    AsyncGenerator,
    Generator,
)
from torch import Tensor


class Capture(NamedTuple):
    data: Tensor
    size: int
    sr: int
    dbpeak: float
    dbrms: float


AudioProcess: TypeAlias = Generator[tuple[int, Capture], int, None]
AssistantProcess: TypeAlias = AsyncGenerator[tuple[Capture, object, BinaryIO], str]


class Broadcast:
    def __init__(self) -> None:
        ...

    def mon(self, peak: float, rms: float, time: float, gate: bool):
        ...

    def clear():
        ...


class EmbeddingData(TypedDict):
    embedding: list
    index: int
    object: str


class EmbeddingUsage(TypedDict):
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(TypedDict):
    data: list[EmbeddingData]
    model: str
    object: str
    usage: EmbeddingUsage


class SystemMessage(TypedDict):
    role: str
    content: str


class ChatMessage(TypedDict):
    role: str
    content: str
    name: str


Messages: TypeAlias = list[SystemMessage | ChatMessage]
