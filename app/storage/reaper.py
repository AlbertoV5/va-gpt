from collections import defaultdict
from typing import NamedTuple
from torchaudio import info
from pathlib import Path
from uuid import uuid4
from time import time
import string
import rpp

no_punctuation = str.maketrans("", "", string.punctuation)


class Base(NamedTuple):
    time: int = int(time())
    children: list = []

    def __repr__(self) -> str:
        return f"""
        <REAPER_PROJECT 0.1 "" {self.time}
            RIPPLE 0
            GROUPOVERRIDE 0 0 0
            AUTOXFADE 1
            {"".join(str(i) for i in self.children)}
        >"""


class Track(NamedTuple):
    name: str
    guid: str = str(uuid4())
    children: list = []

    def __repr__(self):
        return f"""
        <TRACK {{{self.guid}}}
            NAME "{self.name}"
            NCHAN 2
            TRACKID {{{self.guid}}}
            {"".join(str(i) for i in self.children)}
        >"""


class Item(NamedTuple):
    name: str
    length: float
    position: float
    guid: str = str(uuid4())
    children: list = []

    def __repr__(self):
        return f"""
        <ITEM
            POSITION {self.position}
            SNAPOFFS 0
            LENGTH {self.length}
            LOOP 1
            MUTE 0 0
            IGUID {{{self.guid}}}
            NAME {self.name}
            VOLPAN 1 0 1 -1
            SOFFS 0
            GUID {{{self.guid}}}
            {"".join(str(i) for i in self.children)}
        >"""


class Source(NamedTuple):
    format: str
    file: str

    def __repr__(self):
        return f"""
        <SOURCE {self.format}
            FILE {self.file}
        >"""


class Reaper:
    def __init__(self, user: str = "user", assistant: str = "assistant") -> None:
        """Creates RPP projects from audio files metadata."""
        self.user = user
        self.assistant = assistant

    def parse(self, text: str):
        """Load and Dump string"""
        x = "\n".join(i for i in f"{text}".split("\n") if i.split())
        return rpp.dumps(rpp.loads(x), indent=4)

    def get_audio_length(self, filepath: str) -> float:
        """Get length in seconds from path."""
        metadata = info(filepath)
        return metadata.num_frames / metadata.sample_rate

    def iterator(self, sources: dict[str, list[tuple]]):
        """Iterate over both keys."""
        for i, j in zip(sources[self.user], sources[self.assistant]):
            yield self.user, i
            yield self.assistant, j

    def parse_interactions(
        self, sources: dict[str, list[tuple]], offset: float = 0.5
    ) -> dict[str, list]:
        """
        Uses interaction data from the database and returns a dictionary containing the interaction data organized by role.

        Parameters:
            sources (dict[str, list[tuple]]): A dictionary of interaction data, where the keys are the role names ("user" or "assistant"), and the values are lists of tuples containing the data for each interaction. Each tuple should contain the following elements, in order: the interaction ID (an integer), the role name (a string), the filename of the audio file (a string), and the content of the message (a string).
            offset (float): The spacing between the start times of adjacent interactions, in seconds. Defaults to 0.5 seconds.

        Returns:
            dict[str, list]: A dictionary of interaction data, where the keys are the role names ("user" or "assistant"), and the values are lists of `Item` objects representing the interactions. Each `Item` object contains the following fields:
        """
        result = defaultdict(list)
        pos = offset
        t = str.maketrans("", "", string.punctuation)
        # data = (im.int_id, m.role, mf.filename, m.content)
        for role, data in self.iterator(sources):
            path = Path(data[2])
            length = self.get_audio_length(path)
            content = str(data[3]).replace('"', "").replace("\n", "")
            item = Item(
                name=f'"{content}"',
                position=pos,
                length=length,
                children=[Source("VORBIS", path)],
            )
            print(item.name)
            result[role].append(item)
            pos += offset + length
        return result

    def create(self, sources: dict[str, list], filepath: str):
        """
        Creates a `Project` object from message data extracted from the database.

        Args:
            sources: A dictionary with two keys, 'user' and 'assistant', each containing a list
            of filepaths to interaction files to be included in the project.
            filepath: RPP file name to save to disk.
        """
        data = self.parse_interactions(sources)
        project = Base(
            children=[
                Track(name=self.user, children=data[self.user]),
                Track(
                    name=self.assistant,
                    children=data[self.assistant],
                ),
            ]
        )
        with open(filepath, "w") as f:
            f.write(self.parse(project))
