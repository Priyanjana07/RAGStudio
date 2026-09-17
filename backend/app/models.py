from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    documents = relationship("Document", back_populates="owner")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


    owner = relationship("User", back_populates="documents")

    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    text = Column(
        String,
        nullable=False
    )

    chunk_number = Column(
        Integer,
        nullable=False
    )

    page_number = Column(
        Integer,
        nullable=True
    )

    document = relationship(
        "Document",
        back_populates="chunks"
    )
    