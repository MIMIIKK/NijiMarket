from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models.product import Category, Product
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.core.dependencies import require_admin

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    skip: int = Query(0, description="Number of categories to skip"),
    limit: int = Query(100, description="Maximum number of categories to return"),
    active_only: bool = Query(True, description="Show only active categories"),
    db: Session = Depends(get_db)
):
    """Get list of categories."""
    query = db.query(
        Category,
        func.count(Product.id).label("product_count")
    ).outerjoin(Product, Category.id == Product.category_id)
    
    if active_only:
        query = query.filter(Category.is_active == True)
    
    categories = query.group_by(Category.id).offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for category, product_count in categories:
        category_dict = category.__dict__.copy()
        category_dict["product_count"] = product_count or 0
        result.append(CategoryResponse(**category_dict))
    
    return result

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get a specific category by ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Get product count
    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    
    category_dict = category.__dict__.copy()
    category_dict["product_count"] = product_count
    
    return CategoryResponse(**category_dict)

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new category (admin only)."""
    # Check if category with same name already exists
    existing_category = db.query(Category).filter(Category.name == category_data.name).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    # Create new category
    db_category = Category(**category_data.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    category_dict = db_category.__dict__.copy()
    category_dict["product_count"] = 0
    
    return CategoryResponse(**category_dict)

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a category (admin only)."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update category data
    update_data = category_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    # Get product count
    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    category_dict = category.__dict__.copy()
    category_dict["product_count"] = product_count
    
    return CategoryResponse(**category_dict)

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a category (admin only)."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category has products
    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with existing products"
        )
    
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}