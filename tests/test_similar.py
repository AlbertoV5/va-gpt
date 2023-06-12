from app.chat.message import Message, Interaction
from app.system.config import Config
from app.chat.encoder import Encoder
from app.storage import Storage
from sqlalchemy import text
from pathlib import Path
from hashlib import md5
import pickle as pkl
import asyncio
import logging
import pytest

logger = logging.getLogger(__name__)

config = Config.from_toml("config.toml")
encoder = Encoder(config.models.chat.model)
storage = Storage()
storage.load(config.storage)


@pytest.mark.asyncio
async def test_query_message():
    contents = [
        "Hi Vera, what is our template for a new Python project?",
        "Hi Vera, how are you?",
    ]
    msg = Message.new(role="user", name="Beto", content=contents[1])
    exclude_ids = [
        "388574acc0d0201c616c54d4e2cb34c3",
        "75ee67bda3043d3a96b9a7d4fa985b5a",
    ]
    async with storage.db.session() as db:
        logger.info(msg)
        data = await storage.db.read_similar_messages(db, msg.id, exclude_ids=exclude_ids)
        logger.info(data)
        for content in contents:
            msg = Message.new(role="user", name="Beto", content=content)
            filename = f"tests/{msg.id}"
            if Path(filename).exists():
                embedding = pkl.load(open(filename, "rb"))
                logger.info("Loaded embedding from disk")
            else:
                embedding = await storage.embedder.get(content)
                with open(filename, "wb") as f:
                    pkl.dump(embedding, f)
                logger.info("Stored embedding to disk")
            logger.info(content)
            data = await storage.db.read_similar_messages(
                db,
                msg.id,
                embedding=embedding,
                exclude_ids=exclude_ids,
                max_messages=4,
                max_interactions=2,
            )
            logger.info([Interaction.from_db(i) for i in data])


"""
SELECT 
    msg_id,
    embedding <-> (SELECT embedding FROM message_embedding WHERE msg_id = 'ca85117bc90f89e355f25bff4576c2bb') AS "distance"
FROM message_embedding WHERE msg_id != 'ca85117bc90f89e355f25bff4576c2bb'
ORDER BY "distance"
;
"""
# result = await db.execute(text(f"""
# SELECT
#     message.*,
#     message_embedding.embedding <-> '{list(embedding)}'
# FROM message
# JOIN message_embedding
# ON message.id = message_embedding.msg_id
# ORDER BY message_embedding.embedding <-> '{list(embedding)}'
# LIMIT 5;
# """))
# logger.info(result.all())


def main():
    asyncio.run(test_query_message)


if __name__ == "__main__":
    main()
