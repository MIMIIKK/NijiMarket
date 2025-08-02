from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class MarketBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    city: str
    prefecture: str
    country: str = "Japan"
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    market_type: Optional[str] = None
    operating_days: Optional[str] = None  # JSON string
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None

class MarketCreate(MarketBase):
    @validator('operating_days')
    def validate_operating_days(cls, v):
        if v:
            try:
                import json
                days = json.loads(v)
                valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                if not all(day.lower() in valid_days for day in days):
                    raise ValueError('Invalid day in operating_days')
            except json.JSONDecodeError:
                raise ValueError('operating_days must be valid JSON array')
        return v

class MarketUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    prefecture: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    market_type: Optional[str] = None
    operating_days: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    is_active: Optional[bool] = None

class MarketResponse(MarketBase):
    id: int
    is_active: bool
    main_image: Optional[str] = None
    images: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    vendor_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class MarketListResponse(BaseModel):
    id: int
    name: str
    city: str
    prefecture: str
    market_type: Optional[str] = None
    main_image: Optional[str] = None
    is_active: bool
    vendor_count: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    class Config:
        from_attributes = True