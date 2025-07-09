from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(250))
    phone = Column(String(20))
    status = Column(String(20), default="new") # To track leads (new, warm, cold, etc.)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    conversations = relationship("Conversation", back_populates="lead")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    message = Column(Text)
    sender = Column(String(20)) # "customer" or "agent"
    created_at = Column(DateTime, default=datetime.now)

    lead = relationship("Lead", back_populates="conversations")



