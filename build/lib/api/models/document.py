from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from .user import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document_metadata.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    # Using the all-MiniLM-L6-v2 embedding size (384 dimensions)
    embedding = Column(Vector(384))
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentMetadata", backref="chunks")
