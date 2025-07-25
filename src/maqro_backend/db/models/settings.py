from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from maqro_backend.db.base import Base
import pytz

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

    created_at = Column(DateTime, default=datetime.now(pytz.utc))
    updated_at = Column(DateTime, default=datetime.now(pytz.utc), onupdate=datetime.now(pytz.utc))


class AppSettings(Base):
    """Application settings for each dealership and installation"""
    __tablename__ = "app_settings"
    
    id = Column(Integer, primary_key=True) 

    # Follow up email settings
    follow_up_enabled = Column(Boolean, default=True)
    follow_up_delay = Column(Integer, default=24)
    follow_up_interval = Column(Integer, default=72)
    max_follow_ups = Column(Integer, default=3)

    # Business settings
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
    
    created_at = Column(DateTime, default=datetime.now(pytz.utc))
    updated_at = Column(DateTime, default=datetime.now(pytz.utc), onupdate=datetime.now(pytz.utc))