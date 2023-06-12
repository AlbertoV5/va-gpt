from app.chat.message import Message
from app.system.config import Config
from app.chat.encoder import Encoder
from app.storage import Storage
from time import time
import pytest


config = Config.from_toml("config.toml")
encoder = Encoder(config.models.chat.model)
storage = Storage()
storage.load(config.storage)
INTERACTIONS = [
    {
        "interaction_id": 1685858806,
        "created_at": "2023-06-04 01:06:47-05",
        "messages": [
            {
                "role": "user",
                "name": "Beto",
                "content": "Hi Vera, how are you?",
            },
            {
                "role": "assistant",
                "name": "Vera",
                "content": "I'm doing well, Beto. How about you?",
            },
            {
                "role": "user",
                "name": "Beto",
                "content": "All good, thank you. I have been working on a Python program.",
            },
            {
                "role": "assistant",
                "name": "Vera",
                "content": "That's interesting, Beto. What is the Python program for?",
            },
            {
                "role": "user",
                "name": "Beto",
                "content": "I am creating an AI assistant that can be interacted with via voice.",
            },
            {
                "role": "assistant",
                "name": "Vera",
                "content": "That sounds really cool, Beto.",
            },
        ],
    },
    {
        "interaction_id": 1685859151,
        "created_at": "2023-06-04 01:10:47-05",
        "messages": [
            {
                "role": "user",
                "name": "Beto",
                "content": "What is our template for creating a new Python project?",
            },
            {
                "role": "assistant",
                "name": "Vera",
                "content": """
We use these commands to start a new Python project:

```sh
NAME=my-project
VERSION=3.10.10
pyenv install $VERSION
pyenv local $VERSION
python -m venv ./venv
source venv/bin/activate
poetry new $NAME
```
""",
            },
        ],
    },
]


@pytest.mark.asyncio
async def test_add_messages():
    for interaction in INTERACTIONS:
        interaction_id = interaction["interaction_id"]
        messages = create_messages(interaction["messages"])
        print(interaction_id)
        print(messages)
        async with storage.db.session() as db:
            await storage.db.insert_interaction_and_messages(db, interaction_id, messages)
            await db.commit()
        async with storage.db.session() as db:
            for message in messages:
                if message.role == "user":
                    embedding = await storage.embedder.get(message.content)
                    await storage.db.insert_embedding(db, embedding, message.id)
            await db.commit()
        print("All OK")


def create_messages(messages: list[dict]) -> list[Message]:
    result = []
    for message in messages:
        n_tokens = encoder.count(message["content"])
        msg = Message.new(
            role=message["role"],
            content=message["content"],
            name=message["name"],
            n_tokens=n_tokens,
        )
        result.append(msg)
    return result
