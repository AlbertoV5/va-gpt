"""
https://github.com/openai/openai-cookbook/blob/main/examples/How_to_stream_completions.ipynb
"""
from app.chat.message import Message, Interaction, ROLES
from app.system.config import ChatConfig
from app.chat.streamer import Streamer
from app.system.logger import log_json
from app.chat.context import Context

from tiktoken import encoding_for_model

__all__ = ["Chat"]


class Chat:
    """Chat completion flow."""

    short_term: Interaction
    long_term: list[Interaction]

    def __init__(
        self,
        config: ChatConfig,
        context: Context,
    ):
        self.config = config
        self.context = context
        self.streamer = Streamer()
        self.encoder = encoding_for_model(self.config.model)
        # memory
        self.short_term = None
        self.long_term = []
        self.status_ok = None

    def start(self, user_message: Message):
        """Compose a request using short term and long term messages according to set config/context.

        - If the long_term memory contains messages, they will be included in the System message as text.
        - If the short_term memory contains messages, they will be included in the Message as dictionaries.
        - Long and short term memory data varies depending on token limits configuration.
        - Once the request processed, the response content is streamed as blocks of text.
        - Then all messages with the new response are stored in memory for the next request.
        - Then status_ok is set to True if all ok.
        """
        # get updated short term memory for request
        messages = self.get_short_term_messages(user_message)
        self.status_ok = False
        request = {
            "messages": [m.to_api() for m in messages],
            "model": self.config.model,
            "max_tokens": self.config.max_completion_tokens,
            "temperature": self.config.temperature,
            "logit_bias": {
                token: weight
                for text, weight in self.context.assistant.logit_bias.items()
                for token in self.encoder.encode(text)
            },
            "stream": True,
        }
        try:
            # stream response blocks
            blocks = []
            n_tokens = 0
            for block, size in self.streamer.request(request, min_block_size=40):
                yield block
                n_tokens += size
                blocks.append(block)
        except BaseException as e:
            # Log failed completion and return.
            return log_json({"status": "error", "request": request, "exception": str(e)})
        # Add assistant message.
        messages.append(self.assistant_message("".join(blocks), n_tokens))
        # Note, the system message with long term memory content is included.
        self.short_term = Interaction.new(messages)
        self.status_ok = True
        log_json({"status": "ok", "messages": messages})

    def get_short_term_messages(self, user_message: Message):
        """Updates short term memory with list of System message (which includes log term memory text),
        all possible messages in current short term memory based on token count, and latest user message.
        """
        system_message = self.system_message()
        # Current amount of tokens, including max tokens to be requested in completion.
        n_tokens = (
            system_message.n_tokens + user_message.n_tokens + self.config.max_completion_tokens
        )
        if not self.short_term:
            return [system_message, user_message]
        # Get short term memory as (user, assistant) with latest pairs first. Exclude system message (index 0).
        token_limit = self.config.max_total_tokens
        data = self.short_term.messages
        messages = []
        for user, assistant in zip(reversed(data[1::2]), reversed(data[2::2])):
            tokens = assistant.n_tokens + user.n_tokens
            if (n_tokens + tokens) > token_limit:
                break
            n_tokens += tokens
            # Append in reverse order.
            messages.append(assistant)
            messages.append(user)
        # Reverse messages so oldest pair goes first.
        return [system_message, *reversed(messages), user_message]

    def compose_system_context(self):
        """Compose context content from long term memory messages.
        Note that n_tokens start at 0, initial system message token size is not considered."""
        messages = []
        token_limit = self.config.max_system_tokens
        n_tokens = 0
        # Go over all interactions and append message content.
        for interaction in self.long_term:
            messages.append(interaction.created_at.strftime("%Y-%m-%d"))
            # Go over messages as (user, assistant) pairs.
            message_pairs = zip(interaction.messages[0::2], interaction.messages[1::2])
            for user, assistant in message_pairs:
                tokens = assistant.n_tokens + user.n_tokens
                # Return if next message would be over the limit.
                if (n_tokens + tokens) > token_limit:
                    return n_tokens, ("\n".join(messages) if len(messages) > 1 else "")
                n_tokens += tokens
                # Append in regular order.
                messages.append(user.content)
                messages.append(assistant.content)
        return n_tokens, ("\n".join(messages) if len(messages) > 1 else "")

    def system_message(self, with_long_term: bool = True):
        """Create a Message with the System data and long term memory if any."""
        content = self.context.system.message
        n_tokens = len(self.encoder.encode(content))
        # If long term is available, add it to system context alongside header.
        if with_long_term and self.long_term:
            header = self.context.system.context_header
            n_tokens += len(self.encoder.encode(header))
            tokens, context = self.compose_system_context()
            content += f" {header}\n\n{context}" if context else ""
            n_tokens += tokens
        return Message.new(
            role=ROLES.SYSTEM,
            content=content,
            name=None,
            n_tokens=n_tokens,
        )

    def user_message(self, content: str, n_tokens: int = None):
        """Create a message with the User data."""
        return Message.new(
            role=ROLES.USER,
            content=content,
            name=self.context.user.name,
            n_tokens=n_tokens or len(self.encoder.encode(content)),
        )

    def assistant_message(self, content: str, n_tokens: int = None):
        """Create a message with the Assistant data."""
        return Message.new(
            role=ROLES.ASSISTANT,
            content=content,
            name=self.context.assistant.name,
            n_tokens=n_tokens or len(self.encoder.encode(content)),
        )
