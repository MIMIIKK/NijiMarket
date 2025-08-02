from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    
    # Vendor details
    business_name = Column(String, nullable=False)
    business_description = Column(Text)
    specialties = Column(String)  # JSON array of specialties
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verification_documents = Column(String)  # JSON array of document URLs
    
    # Contact and social
    business_phone = Column(String)
    website = Column(String)
    social_media = Column(String)  # JSON object with social links
    
    # Business hours
    available_days = Column(String)  # JSON array of available days
    available_from = Column(String)  # "08:00"
    available_to = Column(String)    # "16:00"
    
    # Rating
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="vendor_profile")
    market = relationship("Market", back_populates="vendors")
    products = relationship("Product", back_populates="vendor")
    bookings = relationship("Booking", back_populates="vendor")
    reviews = relationship("Review", back_populates="vendor")
