from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from maqro_backend.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(250))
    phone = Column(String(20))
    status = Column(String(20), default="new")  # new, warm, cold, converted, lost
    
    # Add follow-up tracking fields
    last_response_at = Column(DateTime, default=datetime.now)
    follow_up_count = Column(Integer, default=0)
    next_follow_up_at = Column(DateTime)
    follow_up_disabled = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    conversations = relationship("Conversation", back_populates="lead")