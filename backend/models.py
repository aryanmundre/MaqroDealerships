from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class DealershipInfo(Base):
    """Basic dealership information for each installation"""
    __tablename__ = "dealership_info"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(250))
    phone = Column(String(20))
    address = Column(String(250))
    website = Column(String(250))
    logo_url = Column(String(250))

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class AppSettings(Base):
    """Application settings for each dealership and installation"""
    __tablename__ = "app_settings"
    
    id = Column(Integer, primary_key=True) 

    # Follow up email settings
    follow_up_enabled = Column(Boolean, default=True)
    follow_up_delay = Column(Integer, default=24)
    follow_up_interval = Column(Integer, default=72)
    max_follow_ups = Column(Integer, default=3)

    # Business settings (fixed typo)
    business_hours_start = Column(String(5), default="09:00")
    business_hours_end = Column(String(5), default="17:00")
    timezone = Column(String(50), default="America/Los_Angeles")
    message_only_on_business_hours = Column(Boolean, default=True)

    # Email settings
    follow_up_subject_template = Column(String(200), default="Following up on your vehicle inquiry")
    follow_up_email_template = Column(Text, default="Hi {customer_name}, we wanted to follow up on your recent inquiry...")

    # AI behavior settings
    ai_response_tone = Column(String(20), default="professional")
    auto_respond_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(250))
    phone = Column(String(20))
    status = Column(String(20), default="new") # new, warm, cold, converted, lost
    
    # Add follow-up tracking fields
    last_response_at = Column(DateTime, default=datetime.now)
    follow_up_count = Column(Integer, default=0)
    next_follow_up_at = Column(DateTime)
    follow_up_disabled = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    conversations = relationship("Conversation", back_populates="lead")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    message = Column(Text)
    sender = Column(String(20)) # "customer", "agent", "system"
    created_at = Column(DateTime, default=datetime.now)

    lead = relationship("Lead", back_populates="conversations")