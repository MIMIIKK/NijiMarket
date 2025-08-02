from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    name_ja = Column(String)  # Japanese translation
    name_ne = Column(String)  # Nepali translation
    description = Column(Text)
    icon = Column(String)  # Icon name or URL
    is_active = Column(Boolean, default=True)
    
    # Relationships
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # Product details
    name = Column(String, nullable=False, index=True)
    name_ja = Column(String)  # Japanese translation
    name_ne = Column(String)  # Nepali translation
    description = Column(Text)
    description_ja = Column(Text)
    description_ne = Column(Text)
    
    # Pricing and availability
    price_per_unit = Column(Float, nullable=False)
    unit = Column(String, nullable=False)  # "kg", "piece", "bunch", etc.
    minimum_order = Column(Float, default=1.0)
    stock_quantity = Column(Float)
    is_available = Column(Boolean, default=True)
    
    # Product characteristics
    is_organic = Column(Boolean, default=False)
    harvest_date = Column(DateTime)
    origin_location = Column(String)
    
    # Images
    main_image = Column(String)
    images = Column(Text)  # JSON array of image URLs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="products")
    category = relationship("Category", back_populates="products")
    booking_items = relationship("BookingItem", back_populates="product")