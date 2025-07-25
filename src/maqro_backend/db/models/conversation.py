from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from maqro_backend.db.base import Base
import pytz


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    message = Column(Text)
    sender = Column(String(20))  # "customer", "agent", "system"
    created_at = Column(DateTime, default=datetime.now(pytz.utc))
    response_time_sec = Column(Integer, nullable=True)

    lead = relationship("Lead", back_populates="conversations")