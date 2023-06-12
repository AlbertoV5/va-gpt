from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import MetaData, ForeignKey, String
from typing_extensions import Annotated
from pgvector.sqlalchemy import Vector
from datetime import datetime


class Base(DeclarativeBase):
    metadata = MetaData(schema="public")


pk_int = Annotated[int, mapped_column(primary_key=True)]
pk_str = Annotated[str, mapped_column(primary_key=True)]


class Message(Base):
    __tablename__ = "message"

    id: Mapped[pk_str] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str]
    name: Mapped[str | None] = mapped_column(String(32))
    n_tokens: Mapped[int]


class MessageEmbedding(Base):
    __tablename__ = "message_embedding"

    msg_id: Mapped[pk_str] = mapped_column(ForeignKey("message.id"))
    embedding = mapped_column(Vector(1536))


class MessageFile(Base):
    __tablename__ = "message_file"

    msg_id: Mapped[pk_str] = mapped_column(ForeignKey("message.id"))
    file_name: Mapped[str] = mapped_column(String(64))


class Interaction(Base):
    __tablename__ = "interaction"

    id: Mapped[pk_int]
    created_at: Mapped[datetime]


class InteractionMessage(Base):
    __tablename__ = "interaction_messages"

    id: Mapped[pk_int] = mapped_column(primary_key=True, autoincrement=True)
    ia_id: Mapped[pk_int] = mapped_column(ForeignKey("interaction.id"))
    msg_id: Mapped[pk_int] = mapped_column(ForeignKey("message.id"))
