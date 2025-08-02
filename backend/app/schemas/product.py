from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.schemas.category import CategoryResponse

class ProductBase(BaseModel):
    name: str
    name_ja: Optional[str] = None
    name_ne: Optional[str] = None
    description: Optional[str] = None
    description_ja: Optional[str] = None
    description_ne: Optional[str] = None
    price_per_unit: float
    unit: str
    minimum_order: float = 1.0
    stock_quantity: Optional[float] = None
    is_organic: bool = False
    harvest_date: Optional[datetime] = None
    origin_location: Optional[str] = None

class ProductCreate(ProductBase):
    category_id: int
    
    @validator('price_per_unit')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v
    
    @validator('minimum_order')
    def validate_minimum_order(cls, v):
        if v <= 0:
            raise ValueError('Minimum order must be greater than 0')
        return v

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    name_ja: Optional[str] = None
    name_ne: Optional[str] = None
    description: Optional[str] = None
    description_ja: Optional[str] = None
    description_ne: Optional[str] = None
    price_per_unit: Optional[float] = None
    unit: Optional[str] = None
    minimum_order: Optional[float] = None
    stock_quantity: Optional[float] = None
    is_available: Optional[bool] = None
    is_organic: Optional[bool] = None
    harvest_date: Optional[datetime] = None
    origin_location: Optional[str] = None
    category_id: Optional[int] = None

class ProductResponse(ProductBase):
    id: int
    vendor_id: int
    category_id: int
    is_available: bool
    main_image: Optional[str] = None
    images: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Relationships
    category: CategoryResponse
    vendor_name: Optional[str] = None
    market_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    id: int
    name: str
    price_per_unit: float
    unit: str
    vendor_id: int
    vendor_name: str
    market_name: str
    category_name: str
    is_available: bool
    is_organic: bool
    main_image: Optional[str] = None
    stock_quantity: Optional[float] = None
    
    class Config:
        from_attributes = True