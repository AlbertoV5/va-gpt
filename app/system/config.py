"""
System configuration.
"""
from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Literal
import pyaudio
import torch
import toml

# ASSISTANT


class WakeUpConfig(BaseModel):
    triggers: list[str]
    include_assistant_name: bool
    awake_seconds: float = Field(ge=0)

    @validator("triggers")
    def lowercase_triggers(cls, x: list[str]):
        return [i.lower() for i in x]


class SleepConfig(BaseModel):
    triggers: list[str]

    @validator("triggers")
    def lowercase_triggers(cls, x: list[str]):
        return [i.lower() for i in x]


class AssistantConfig(BaseModel):
    wakeup: WakeUpConfig
    sleep: SleepConfig


# MODELS


class ChatConfig(BaseModel):
    model: str
    max_completion_tokens: int
    max_total_tokens: int
    max_system_tokens: int
    temperature: float


class TranscribeConfig(BaseModel):
    model: str
    language: str
    fp16: bool
    initial_prompt: str
    include_assistant_name: bool


class ModelsConfig(BaseModel):
    chat: ChatConfig
    transcribe: TranscribeConfig


# AUDIO

BITRATE_DTYPE = {16: torch.int16, 32: torch.int32}
BITRATE_SPLFRMT = {16: pyaudio.paInt16, 32: pyaudio.paInt32}
BITRATE_CEIL = {16: 65536 // 2, 32: 4294967296 // 2}


class ChannelConfig(BaseModel):
    chunk: Literal[256, 512, 1024, 2048, 4096, 8192] = 2048
    samplerate: Literal[8000, 16000, 24000] = 2400
    bitrate: Literal[16, 32] = 16
    refreshrate_hz: float = Field(ge=1.0, le=5.0)

    _whisper_sr: Literal[16000] = 16000

    @property
    def dtype(self):
        """Torch type"""
        return BITRATE_DTYPE[self.bitrate]

    @property
    def splformat(self):
        """Sample format for pyaudio"""
        return BITRATE_SPLFRMT[self.bitrate]

    @property
    def fullscale(self):
        """Get the full scale value from bitrate. 2 ** {bitrate} // 2"""
        return BITRATE_CEIL[self.bitrate]


class GateConfig(BaseModel):
    dbpeak: float = Field(ge=-60, le=0)
    dbrms: float = Field(ge=-60, le=0)
    hold_sec: float = Field(ge=1.0, le=5.0)
    tail_sec: float = Field(ge=1.0, le=5.0)


class AudioConfig(BaseModel):
    channel: ChannelConfig
    gate: GateConfig


# STORAGE


class DatabaseConfig(BaseModel):
    dbpath: str
    embedder: str


class FilesConfig(BaseModel):
    directory: str
    subpath_frmt: str
    record_audio: bool
    subpath: datetime = Field(default_factory=datetime.now)


class StorageConfig(BaseModel):
    database: DatabaseConfig
    files: FilesConfig


class Config(BaseModel):
    assistant: AssistantConfig
    models: ModelsConfig
    audio: AudioConfig
    storage: StorageConfig

    @classmethod
    def from_toml(cls, filename: str):
        """Load config from TOML file."""
        with open(filename, "r") as f:
            return Config(**toml.loads(f.read()))
