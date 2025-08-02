from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.schemas.user import UserResponse

class VendorBase(BaseModel):
    business_name: str
    business_description: Optional[str] = None
    specialties: Optional[str] = None  # JSON array
    business_phone: Optional[str] = None
    website: Optional[str] = None
    social_media: Optional[str] = None  # JSON object
    available_days: Optional[str] = None  # JSON array
    available_from: Optional[str] = None
    available_to: Optional[str] = None

class VendorCreate(VendorBase):
    market_id: int
    
    @validator('specialties')
    def validate_specialties(cls, v):
        if v:
            try:
                import json
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('specialties must be valid JSON array')
        return v

class VendorUpdate(BaseModel):
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    specialties: Optional[str] = None
    business_phone: Optional[str] = None
    website: Optional[str] = None
    social_media: Optional[str] = None
    available_days: Optional[str] = None
    available_from: Optional[str] = None
    available_to: Optional[str] = None
    market_id: Optional[int] = None

class VendorResponse(VendorBase):
    id: int
    user_id: int
    market_id: int
    is_verified: bool
    average_rating: float
    total_reviews: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Relationships
    user: UserResponse
    market_name: Optional[str] = None
    product_count: int = 0
    
    class Config:
        from_attributes = True

class VendorListResponse(BaseModel):
    id: int
    business_name: str
    market_id: int
    market_name: str
    is_verified: bool
    average_rating: float
    total_reviews: int
    specialties: Optional[str] = None
    
    class Config:
        from_attributes = True

class VendorProfileResponse(VendorResponse):
    products: Optional[List] = []  # Will be populated with products