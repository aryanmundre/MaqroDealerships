"""
SQLAlchemy models for Supabase integration

These models match the Supabase schema defined in frontend/supabase/schema.sql
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Lead(Base):
    """Lead model matching Supabase leads table schema"""
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(Text, nullable=False)
    car = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    status = Column(Text, nullable=False)  # 'new', 'warm', 'hot', 'follow-up', 'cold'
    last_contact = Column(Text, nullable=False)
    email = Column(Text)
    phone = Column(Text)
    message = Column(Text)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    # Relationships
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation model for storing messages between leads and agents"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    message = Column(Text, nullable=False)
    sender = Column(Text, nullable=False)  # 'customer' or 'agent'

    # Relationships
    lead = relationship("Lead", back_populates="conversations")


class Inventory(Base):
    """Inventory model matching Supabase inventory table schema"""
    __tablename__ = "inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    make = Column(Text, nullable=False)
    model = Column(Text, nullable=False)
    year = Column(Integer, nullable=False)
    price = Column(String, nullable=False)  # Using String to match DECIMAL(10,2)
    mileage = Column(Integer)
    description = Column(Text)
    features = Column(Text)
    dealership_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Text, default="active")  # 'active', 'sold', 'pending'


class UserProfile(Base):
    """User profile model matching Supabase user_profiles table schema"""
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    full_name = Column(Text)
    phone = Column(Text)
    role = Column(Text)
    timezone = Column(Text, default="America/New_York")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
