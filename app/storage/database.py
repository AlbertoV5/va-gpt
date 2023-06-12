from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import func, select, text, extract, alias
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from typing import Callable

from app.storage.schema import (
    InteractionMessage,
    MessageEmbedding,
    Interaction,
    MessageFile,
    Message,
)
from app.chat.message import (
    Message as MessageData,
    Interaction as InteractionData,
    ROLES,
)
from app.system.config import DatabaseConfig
from app.system.logger import log_json


class Database:
    session: Callable[[], AsyncSession]

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = create_async_engine(f"postgresql+asyncpg://{config.dbpath}")
        self.session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    # async def read_from_dates(
    #     self,
    #     from_date: datetime,
    #     to_date: datetime,
    # ):
    #     messages = {"assistant": [], "user": []}

    #     async with self.session() as db:
    #         for role in messages.keys():
    #             result = await db.execute(
    #                 text(
    #                     f"""
    #                 SELECT im.ia_id, m.role, m.file, m.content
    #                 FROM interaction_messages AS im
    #                 JOIN message AS m
    #                     ON m.id = im.msg_id
    #                 JOIN interaction AS i
    #                     ON i.id = im.ia_id
    #                 WHERE im.created_on > {from_date}
    #                 AND im.created_on < {to_date}
    #                 AND m.role = {role}
    #                 ;
    #             """
    #                 )
    #             )
    #             messages[role] = result.all()
    #     return messages

    # async def read_latest(self):
    #     """Read latest interactions."""
    #     async with self.session() as db:
    #         result = await db.execute(
    #             text(
    #                 """
    #             WITH latest AS
    #             (
    #                 SELECT ia_id
    #                 FROM interaction
    #                 ORDER BY ia_id
    #                 DESC LIMIT 1
    #             )
    #             SELECT m.role, m.content
    #             FROM interaction_messages AS im
    #             JOIN message AS m
    #             ON m.id = im.msg_id
    #             WHERE im.ia_id = (SELECT * FROM latest)
    #             AND m.role = 'user' OR m.role = 'assistant'
    #             ;
    #             """
    #             )
    #         )
    #         result = result.all()
    #         if len(result) > 0:
    #             return [{"role": m[0], "content": m[1]} for m in result]

    async def insert_interaction_and_messages(
        self,
        db: AsyncSession,
        ia_id: int,
        messages: list[MessageData],
    ):
        """Insert interaction and messages."""
        data = [m.to_db() for m in messages]
        await db.execute(
            insert(Interaction).on_conflict_do_nothing(),
            {"id": ia_id},
        )
        await db.execute(insert(Message).on_conflict_do_nothing(), data)
        # insert interaction messages
        data = [{"ia_id": ia_id, "msg_id": m.id} for m in messages]
        await db.execute(insert(InteractionMessage).on_conflict_do_nothing(), data)
        await db.commit()

    async def insert_message_embedding(self, db: AsyncSession, message_id: str, embedding: list):
        """Insert message embedding."""
        data = {"msg_id": message_id, "embedding": embedding}
        await db.execute(insert(MessageEmbedding).on_conflict_do_nothing(), data)
        await db.commit()

    async def insert_message_file(
        self,
        db: AsyncSession,
        message_id: list[str],
        files: list[str],
    ):
        """Insert message files."""
        data = [{"msg_id": m, "file_name": f} for m, f in zip(message_id, files)]
        await db.execute(insert(MessageFile).on_conflict_do_nothing(), data)
        await db.commit()

    async def insert_embedding(self, db: AsyncSession, embedding: list, msg_id: str):
        """Insert embedding."""
        data = {"embedding": embedding, "msg_id": msg_id}
        await db.execute(insert(MessageEmbedding).on_conflict_do_nothing(), data)
        await db.commit()

    async def read_embedding(self, db: AsyncSession, message_id: str):
        """Read message embedding."""
        result = await db.execute(
            select(MessageEmbedding.embedding).where(MessageEmbedding.msg_id == message_id)
        )
        return result.scalar()

    async def read_similar_messages(
        self,
        db: AsyncSession,
        msg_id: str,
        *,
        embedding: list = None,
        exclude_ids: list[str] = None,
        max_messages: int = 4,
        max_interactions: int = 1,
        round_by: int = 2,
    ):
        """Get a list of interactions from the most similar messages.
        Use msg_id to find the embedding of an existing message or use new embedding if given.

        - Provide a list of msg ids to exclude from the similarity search. This helps whenever
        those msg ids are already in memory and included in the completion.
        - Max messages dictates how many messages from the similarity search are used
        to find interactions where those messages are present.
        - Max interactions dictates how many of those interactions are returned.
        - Round by defines the decimals to round the distance to in order to "stair"
        the results. If two interactions have the same distance, the most recent is returned.

        The return shape is (interaction_id, created_at, distance, message[], n_tokens[]).
        Where message is (id, role, name, content) and n_tokens contains their respective n_tokens.
        """
        # Short circuit function if there is no embedding source.
        if embedding is None and (await db.get(MessageEmbedding, msg_id)) is None:
            return None
        # Exclude msg_id to prevent self-similarity.
        exclude = ", ".join(f"'{id}'" for id in [msg_id, *(exclude_ids or [])])
        if embedding is None:
            # Get all message ids sorted by similarity to an existing message in database.
            query_messages = f"""
                SELECT
                    msg_id,
                    ROUND((embedding <=>
                        (SELECT embedding FROM message_embedding WHERE msg_id = '{msg_id}'))
                        ::numeric, {round_by}) AS "distance"
                FROM message_embedding
                WHERE msg_id NOT IN ({exclude})
                ORDER BY "distance"
            """
        else:
            # Get all message ids sorted by similarity to a new embedding.
            # cosine
            # ROUND((embedding <=> '{embedding}')::numeric, {round_by}) AS "distance"
            # euclidean
            # ROUND((embedding <-> '{embedding}')::numeric, {round_by}) AS "distance"
            query_messages = f"""
                SELECT
                    msg_id,
                    ROUND((embedding <=> '{embedding}')::numeric, {round_by}) AS "distance"
                FROM message_embedding
                WHERE msg_id NOT IN ({exclude})
                ORDER BY "distance"
            """
        # Get all interaction ids where the message ids are present, sorted by date.
        query_interactions = f"""
            WITH selected_messages AS (
                {query_messages}
                LIMIT {max_messages}
            )
            SELECT
                interaction_messages.ia_id,
                selected_messages.distance
            FROM selected_messages
            JOIN interaction_messages
            ON selected_messages.msg_id = interaction_messages.msg_id
            JOIN interaction
            ON interaction.id = interaction_messages.ia_id
            WHERE selected_messages.distance IS NOT NULL
            GROUP BY (interaction_messages.ia_id, interaction.created_at, selected_messages.distance)
            ORDER BY (-selected_messages.distance, interaction.created_at) DESC
            LIMIT {max_interactions}
        """
        # Get all messages present in the interaction ids, sorted by date and im id.
        query = f"""
        WITH selected_interactions AS (
            {query_interactions}
        )
        SELECT
            selected_interactions.ia_id AS "interaction_id",
            interaction.created_at AS "created_at",
            selected_interactions.distance AS "distance",
            ARRAY_AGG(
                ARRAY[message.id, message.role, message.content, message.name] 
            ) AS "messages",
            ARRAY_AGG(
                message.n_tokens
            ) AS "n_tokens"
        FROM message
        JOIN interaction_messages
            ON interaction_messages.msg_id = message.id
        JOIN interaction
            ON interaction_messages.ia_id = interaction.id
        JOIN selected_interactions
            ON selected_interactions.ia_id = interaction.id
        AND message.role != '{ROLES.SYSTEM}'
        GROUP BY selected_interactions.ia_id, interaction.created_at, selected_interactions.distance
        ORDER BY (-selected_interactions.distance, interaction.created_at) DESC
        ;
        """
        result = await db.execute(text(query))
        return result.all()
