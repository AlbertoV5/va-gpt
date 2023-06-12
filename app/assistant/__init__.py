from app.assistant.commands import Commands
from app.speech import Speech, VoiceStyle
from app.chat import Chat, Context
from app.system.config import Config
from app.broadcast import Broadcast

from app.audio import AudioChannel, Transcribe
from app.storage import Storage


class Assistant:
    """Voice Assistant using transcription models, chat completion, and Speech Synthesis."""

    channel: AudioChannel
    broadcast: Broadcast
    context: Context
    commands: Commands
    voice: VoiceStyle
    storage: Storage

    def __init__(self) -> None:
        pass

    def load(
        self,
        config: Config,
        voice: VoiceStyle,
        context: Context,
    ):
        """Load configuration to all submodules."""
        # config
        self.voice = voice
        self.context = context
        self.config = config.assistant
        SR = config.audio.channel.samplerate
        # models
        self.speech = Speech(voice, SR)
        self.chat = Chat(config.models.chat, context)
        self.transcribe = Transcribe(config.models.transcribe, SR)
        # flow
        self.exit = False
        self.awake = False
        self.attend_spls = self.config.wakeup.awake_seconds * SR
        self.notes = ""
        # triggers
        self.wakeup_words = self.config.wakeup.triggers
        self.sleep_words = self.config.sleep.triggers
        if self.config.wakeup.include_assistant_name:
            self.wakeup_words.append(self.context.assistant.name.lower())
        if config.models.transcribe.include_assistant_name:
            self.transcribe.update_initial_prompt(self.context.assistant.name)

    async def start(self):
        """Listen for prompts from the audio process.

        Process:
            - Whenever the audio process yields a capture, transcribe it.
            - If the prompt contains a command, execute it and dispatch.
            - If the prompt contains a sleep word, set to sleep and dispatch.
            - If the prompt contains an attend word or assistant is awake, enter chat.
            - Prompt chat including assistant's notes.
            - Synthesize speech from chat response.
            - Play audio file and store interaction in database.
        """
        # Add audio recorder to storage.
        self.storage.recorder = self.channel.recorder
        # Initialize audio process.
        audio_process = self.channel.start(self.broadcast, self.attend_spls)
        # Expects sample position and audio capture.
        for spls, capture in audio_process:
            # Transcribe capture.
            for _ in self.broadcast.loading(":pencil:"):
                self.prompt = self.transcribe.predict(capture.data)
            self.broadcast.clear()
            # Nothing was transcribed.
            if not self.prompt:
                ...
            # Execute command if found in prompt.
            elif (result := await self.commands.execute(self.prompt)) is not None:
                self.broadcast.command(self.prompt, result)
            # Go to sleep if found in prompt. Set sample position to max.
            elif self.sleep:
                self.broadcast.sleep(self.prompt)
                spls = self.attend_spls
            # Initialize interaction if assistant is awake or if prompt wakes it up.
            elif (self.awake and self.attend_spls > spls) or self.wakeup:
                user_message = self.chat.user_message(f"{self.prompt}{self.notes}")
                # Get similar messages from database and pass them to the chat.
                self.chat.long_term = await self.storage.read_similar(
                    user_message, exclude=self.chat.short_term
                )
                self.broadcast.user(f"{self.prompt} ({user_message.n_tokens})")
                # Stream response blocks, broadcast and play audio.
                for block in self.broadcast.assistant(self.chat.start(user_message)):
                    file = self.speech.synthesize(block)
                    self.channel.recorder.to_tape(file)
                    self.channel.player.queue(file)
                # Store interaction if chat was successful.
                if self.chat.status_ok:
                    # Store audio files if enabled and insert db records.
                    self.storage.store_audiofiles(self.chat.short_term, capture)
                    await self.storage.store_interaction(self.chat.short_term)
                    # Restart audio sample position and assistant's notes.
                    spls, self.notes = 0, ""
            else:
                # Broadcast capture and send sample position back to audio process.
                self.broadcast.capture(capture, self.prompt)
            if self.exit:
                raise KeyboardInterrupt
            audio_process.send(spls)

    def stop(self):
        """Stop the assistant."""
        self.exit = True

    @property
    def wakeup(self):
        """Check if any of the wakeup words are in prompt. Lower case."""
        prompt = self.prompt.lower()
        for word in self.wakeup_words:
            if word in prompt:
                self.awake = True
                return True
        return False

    @property
    def sleep(self):
        """Check if any of the sleep words are in prompt, if True, set awake to False."""
        prompt = self.prompt.lower()
        for word in self.sleep_words:
            if word in prompt:
                self.awake = False
                return True
        return False

    @property
    def commands(self) -> Commands:
        return self._commands

    @commands.setter
    def commands(self, data: dict):
        self._commands = Commands(data)
