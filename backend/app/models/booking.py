from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    consumer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Booking details
    booking_number = Column(String, unique=True, nullable=False, index=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    
    # Pickup details
    preferred_pickup_date = Column(DateTime, nullable=False)
    preferred_pickup_time = Column(String)  # "10:00-11:00"
    actual_pickup_time = Column(DateTime)
    
    # Pricing
    total_amount = Column(Float, nullable=False)
    
    # Notes
    consumer_notes = Column(Text)
    vendor_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    consumer = relationship("User", back_populates="bookings")
    vendor = relationship("Vendor", back_populates="bookings")
    market = relationship("Market", back_populates="bookings")
    items = relationship("BookingItem", back_populates="booking")
    review = relationship("Review", back_populates="booking", uselist=False)

class BookingItem(Base):
    __tablename__ = "booking_items"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relationships
    booking = relationship("Booking", back_populates="items")
    product = relationship("Product", back_populates="booking_items")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    consumer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    
    # Review details
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)
    
    # Review categories
    quality_rating = Column(Integer)
    service_rating = Column(Integer)
    value_rating = Column(Integer)
    
    is_verified = Column(Boolean, default=False)  # Verified purchase
    is_approved = Column(Boolean, default=True)   # Admin approval
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    consumer = relationship("User", back_populates="reviews")
    vendor = relationship("Vendor", back_populates="reviews")
    booking = relationship("Booking", back_populates="review")