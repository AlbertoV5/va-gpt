"""
Type Aliases and Protocols only.
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/polly.html#polly
"""

from typing import Literal, Protocol, TypedDict, TypeAlias

PollyEngine: TypeAlias = Literal["standard", "neural"]

PollyLang: TypeAlias = Literal[
    "arb",
    "cmn-CN",
    "cy-GB",
    "da-DK",
    "de-DE",
    "en-AU",
    "en-GB",
    "en-GB-WLS",
    "en-IN",
    "en-US",
    "es-ES",
    "es-MX",
    "es-US",
    "fr-CA",
    "fr-FR",
    "is-IS",
    "it-IT",
    "ja-JP",
    "hi-IN",
    "ko-KR",
    "nb-NO",
    "nl-NL",
    "pl-PL",
    "pt-BR",
    "pt-PT",
    "ro-RO",
    "ru-RU",
    "sv-SE",
    "tr-TR",
    "en-NZ",
    "en-ZA",
    "ca-ES",
    "de-AT",
    "yue-CN",
    "ar-AE",
    "fi-FI",
]
PollyVoiceId: TypeAlias = Literal[
    "Aditi",
    "Amy",
    "Astrid",
    "Bianca",
    "Brian",
    "Camila",
    "Carla",
    "Carmen",
    "Celine",
    "Chantal",
    "Conchita",
    "Cristiano",
    "Dora",
    "Emma",
    "Enrique",
    "Ewa",
    "Filiz",
    "Gabrielle",
    "Geraint",
    "Giorgio",
    "Gwyneth",
    "Hans",
    "Ines",
    "Ivy",
    "Jacek",
    "Jan",
    "Joanna",
    "Joey",
    "Justin",
    "Karl",
    "Kendra",
    "Kevin",
    "Kimberly",
    "Lea",
    "Liv",
    "Lotte",
    "Lucia",
    "Lupe",
    "Mads",
    "Maja",
    "Marlene",
    "Mathieu",
    "Matthew",
    "Maxim",
    "Mia",
    "Miguel",
    "Mizuki",
    "Naja",
    "Nicole",
    "Olivia",
    "Penelope",
    "Raveena",
    "Ricardo",
    "Ruben",
    "Russell",
    "Salli",
    "Seoyeon",
    "Takumi",
    "Tatyana",
    "Vicki",
    "Vitoria",
    "Zeina",
    "Zhiyu",
    "Aria",
    "Ayanda",
    "Arlet",
    "Hannah",
    "Arthur",
    "Daniel",
    "Liam",
    "Pedro",
    "Kajal",
    "Hiujin",
    "Laura",
    "Elin",
    "Ida",
    "Suvi",
    "Ola",
    "Hala",
    "Andres",
    "Sergio",
    "Remi",
    "Adriano",
    "Thiago",
    "Ruth",
    "Stephen",
    "Kazuha",
    "Tomoko",
]


class StreamingBody(Protocol):
    def close():
        ...

    def read():
        ...


class ResponseData(TypedDict):
    AudioStream: StreamingBody
    ContentType: str
    RequestCharacters: int


class PollyClient(Protocol):
    def synthesize_speech(
        self,
        Engine: PollyEngine,
        LanguageCode: PollyLang,
        OutputFormat: Literal["json", "mp3", "ogg_vorbis", "pcm"],
        SampleRate: str,
        Text: str,
        TextType: Literal["ssml", "text"],
        VoiceId: PollyVoiceId,
    ) -> ResponseData:
        ...
