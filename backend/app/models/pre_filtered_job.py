"""
Pre-filtered job model for tracking jobs excluded before LLM parsing.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class PreFilteredJob(Base):
    """Pre-filtered job model."""

    __tablename__ = "pre_filtered_jobs"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String)
    snippet = Column(Text)
    source_domain = Column(String, index=True)
    filter_reason = Column(String, index=True)
    filter_details = Column(Text)
    raw_content_preview = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

