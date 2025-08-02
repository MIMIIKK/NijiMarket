from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Market(Base):
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    
    # Location
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    prefecture = Column(String, nullable=False)
    country = Column(String, default="Japan")
    postal_code = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Market details
    market_type = Column(String)  # "farmers", "organic", "traditional", etc.
    is_active = Column(Boolean, default=True)
    
    # Operating hours
    operating_days = Column(String)  # JSON string: ["monday", "wednesday", "saturday"]
    opening_time = Column(String)    # "08:00"
    closing_time = Column(String)    # "16:00"
    
    # Images and media
    main_image = Column(String)
    images = Column(Text)  # JSON array of image URLs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    vendors = relationship("Vendor", back_populates="market")
    bookings = relationship("Booking", back_populates="market")
