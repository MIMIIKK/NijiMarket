from pydantic import BaseModel
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    name_ja: Optional[str] = None
    name_ne: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    name_ja: Optional[str] = None
    name_ne: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryResponse(CategoryBase):
    id: int
    is_active: bool
    product_count: int = 0
    
    class Config:
        from_attributes = True