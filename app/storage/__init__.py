from pathlib import Path

from app.storage.database import Database
from app.storage.embedder import Embedder
from app.storage.reaper import Reaper

from app.chat.message import Message, Interaction
from app.system.config import StorageConfig
from app.audio import Capture, Recorder


class Storage:
    recorder: Recorder
    """Pointer to audio recorder"""

    def __init__(self):
        pass

    def load(self, config: StorageConfig):
        self.embedder = Embedder(config.database.embedder)
        self.db = Database(config.database)
        self.rpp = Reaper()
        # file storage
        self.record_audio = config.files.record_audio
        self.files = config.files
        # secondary data
        self.embedding_cache = None
        self.audiofiles_cache = None

    @property
    def directory(self) -> Path:
        """Get path, create it if it doesn't exist."""
        subpath = self.files.subpath.strftime(self.files.subpath_frmt)
        path = Path(self.files.directory) / subpath
        if not path.is_dir():
            path.mkdir(parents=True)
        return path

    async def read_similar(self, message: Message, exclude: Interaction = None):
        """Look for similar message in database.
        If message is not found, generate new embeddings and use them to find similar message.
        Return similar message.
        """
        exclude_ids = [m.id for m in exclude.messages] if exclude else []
        async with self.db.session() as session:
            result = await self.db.read_similar_messages(
                session, message.id, exclude_ids=exclude_ids
            )
            # if message is not found, generate new embeddings
            if not result:
                embedding = await self.embedder.get(message.content)
                self.embedding_cache = (message.id, embedding)
                result = await self.db.read_similar_messages(
                    session, message.id, embedding=embedding, exclude_ids=exclude_ids
                )
        # parse database results
        return [Interaction.from_db(r) for r in result]

    async def store_interaction(self, interaction: Interaction):
        """Store messages in database."""
        async with self.db.session() as db:
            # insert to message, interaction, and interaction_message tables
            await self.db.insert_interaction_and_messages(db, interaction.id, interaction.messages)
            # insert to message_embedding table
            if self.embedding_cache is not None:
                await self.db.insert_message_embedding(db, *self.embedding_cache)
                self.embedding_cache = None
            # insert to message_file table
            if self.audiofiles_cache is not None:
                await self.db.insert_message_file(db, *self.audiofiles_cache)
                self.audiofiles_cache = None

    def store_audiofiles(self, interaction: Interaction, capture: Capture):
        """Store audiofiles in directory. Uses the ids of the last two messages in interaction."""
        if self.files.record_audio:
            # create filepath from timestamp
            path = self.directory / str(interaction.id)
            f1 = self.recorder.save(capture.data, f"{path}_1.ogg")
            f2 = self.recorder.save_tape(f"{path}_2.ogg")
            # extract user id and assistant id from last two messages
            self.audiofiles_cache = ([m.id for m in interaction.messages[-2:]], [f1, f2])
