"""
SQLAlchemy ORM models for the Bias Detector application.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from database import Base


class Analysis(Base):
    """Stores every completed article analysis for history retrieval."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False, default="Untitled")
    url = Column(String(2000), nullable=True)
    input_text = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)  # Full JSON result stored as text

    # Denormalized scores for quick history queries
    bias_label = Column(String(20), nullable=True)
    bias_score = Column(Integer, nullable=True)
    emotion_score = Column(Integer, nullable=True)
    factual_score = Column(Integer, nullable=True)

    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Analysis(id={self.id}, title='{self.title[:30]}', bias={self.bias_label})>"
