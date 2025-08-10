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
    car_interest = Column(Text, nullable=False)  # Renamed from 'car' to support types like 'sedan', 'Toyota Camry sedan'
    source = Column(Text, nullable=False)
    status = Column(Text, nullable=False)  # 'new', 'warm', 'hot', 'follow-up', 'cold', 'appointment_booked', 'deal_won', 'deal_lost'
    last_contact_at = Column(DateTime(timezone=True), nullable=False)
    email = Column(Text)
    phone = Column(Text)
    message = Column(Text)
    deal_value = Column(String)  # Using String to match DECIMAL(10,2)
    max_price = Column(Text)  # Maximum price range for the lead (flexible text format)
    appointment_datetime = Column(DateTime(timezone=True))
    user_id = Column(UUID(as_uuid=True))  # Assigned salesperson (nullable)
    dealership_id = Column(UUID(as_uuid=True), ForeignKey("dealerships.id"), nullable=False)

    # Relationships
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    dealership = relationship("Dealership", back_populates="leads")


class Conversation(Base):
    """Conversation model for storing messages between leads and agents"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    message = Column(Text, nullable=False)
    sender = Column(Text, nullable=False)  # 'customer', 'agent', or 'system'

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
    condition = Column(Text)  # Physical condition of the vehicle (excellent, good, fair, poor, etc.)
    dealership_id = Column(UUID(as_uuid=True), ForeignKey("dealerships.id"), nullable=False)
    status = Column(Text, default="active")  # 'active', 'sold', 'pending'

    # Relationships
    dealership = relationship("Dealership", back_populates="inventory")


class UserProfile(Base):
    """User profile model matching Supabase user_profiles table schema"""
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    dealership_id = Column(UUID(as_uuid=True), ForeignKey("dealerships.id"))
    full_name = Column(Text)
    phone = Column(Text)
    role = Column(Text)  # 'admin', 'salesperson'
    timezone = Column(Text, default="America/New_York")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    dealership = relationship("Dealership", back_populates="user_profiles")


class Dealership(Base):
    """Dealership model for storing organization-level data"""
    __tablename__ = "dealerships"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    name = Column(Text, nullable=False)
    location = Column(Text)
    # crm_api_key = Column(Text) # Note: Should be encrypted at rest

    # Relationships
    user_profiles = relationship("UserProfile", back_populates="dealership")
    inventory = relationship("Inventory", back_populates="dealership")
    leads = relationship("Lead", back_populates="dealership")
