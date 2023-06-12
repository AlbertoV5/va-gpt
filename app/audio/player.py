from subprocess import Popen, PIPE
from threading import Thread
from typing import BinaryIO

from app.system.logger import log_json


class Player:
    """Audio player using ffmpeg"""

    def __init__(self) -> None:
        self.is_playing = False
        self.threads: list[Thread] = []

    def queue(self, file: BinaryIO):
        """Queue file for playback. Start playback thread if not already started."""
        if file is None:
            return log_json({"error": "Can't play None file."})
        self.threads.append(Thread(target=self._ffplay, args=[file]))
        # go over all threads
        while self.threads:
            if not self.is_playing:
                thread = self.threads.pop()
                thread.start()
                break

    def _ffplay(self, file: BinaryIO):
        """Playback files in queue using ffmpeg."""
        # ['ffmpeg', '-i', 'pipe:', '-f', 'wav', '-ar', f'{SR}', 'pipe:']
        cmd = [
            "ffplay",
            "-f",
            "ogg",
            "-i",
            "-",
            "-autoexit",
            "-nodisp",
            "-loglevel",
            "quiet",
        ]
        self.is_playing = True
        file.seek(0)
        proc = Popen(cmd, stdout=PIPE, stdin=PIPE)
        proc.communicate(input=file.read())
        proc.wait()
        file.close()
        self.is_playing = False
