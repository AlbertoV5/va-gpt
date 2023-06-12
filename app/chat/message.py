"""
Dictionary wrapper for requests and storage.
"""
from typing import NamedTuple
from datetime import datetime
from hashlib import md5
from time import time


class ROLES:
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


ROLE_ID = {
    ROLES.SYSTEM: 0,
    ROLES.USER: 1,
    ROLES.ASSISTANT: 2,
}


class Message(NamedTuple):
    id: str
    role: str
    content: str
    name: str = None
    n_tokens: int = None

    @classmethod
    def new(
        cls,
        role: str,
        content: str,
        name: str = None,
        n_tokens: int = None,
    ) -> "Message":
        """Creates a new message with a md5 id of the contents."""
        id = md5(f"{role}:{content}:{name or ''}".encode()).hexdigest()
        return Message(id, role, content, name, n_tokens)

    @property
    def role_id(self):
        """Probably not used right now."""
        return ROLE_ID[self.role]

    def to_api(self):
        """Construct a dictionary compatible with API schema."""
        return (
            {
                "role": self.role,
                "content": self.content,
                "name": self.name,
            }
            if self.name
            else {
                "role": self.role,
                "content": self.content,
            }
        )

    def to_db(self):
        """Construct a dictionary compatible with database schema."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "n_tokens": self.n_tokens,
        }


class Interaction(NamedTuple):
    """Database query result for an interaction with multiple messages."""

    id: int
    messages: list[Message]
    created_at: datetime = None
    distance: float = None

    @classmethod
    def new(cls, messages: list[Message]) -> "Interaction":
        """Creates a new interaction with a list of messages and id of current unix timestamp."""
        return cls(
            id=int(time()),
            messages=messages,
            created_at=None,
            distance=None,
        )

    @classmethod
    def from_db(cls, data: tuple) -> "Interaction":
        """Creates an interaction from a database query result.
        The result is a tuple of:
            - data[0] = interaction_id
            - data[1] = created_at
            - data[2] = distance
            - data[3] = [messages] (id, role, content, name)
            - data[4] = [n_tokens] (for each message in messages)
        And n_tokens is the number of tokens in the messages.
        """
        return cls(
            id=data[0],
            created_at=data[1],
            distance=data[2],
            messages=[Message(*m, nt) for m, nt in zip(data[3], data[4])],
        )
