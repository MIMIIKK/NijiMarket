from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models.vendor import Vendor
from app.models.market import Market
from app.models.user import User, UserRole
from app.models.product import Product
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse, VendorListResponse
from app.core.dependencies import (
    get_current_active_user, 
    require_admin, 
    require_vendor_or_admin
)

router = APIRouter(prefix="/vendors", tags=["Vendors"])

@router.get("/", response_model=List[VendorListResponse])
def get_vendors(
    skip: int = Query(0, description="Number of vendors to skip"),
    limit: int = Query(100, description="Maximum number of vendors to return"),
    market_id: Optional[int] = Query(None, description="Filter by market ID"),
    verified_only: bool = Query(False, description="Show only verified vendors"),
    db: Session = Depends(get_db)
):
    """Get list of vendors with optional filters."""
    query = db.query(Vendor, Market.name.label("market_name")).join(
        Market, Vendor.market_id == Market.id
    )
    
    # Apply filters
    if market_id:
        query = query.filter(Vendor.market_id == market_id)
    if verified_only:
        query = query.filter(Vendor.is_verified == True)
    
    vendors = query.offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for vendor, market_name in vendors:
        vendor_dict = {
            "id": vendor.id,
            "business_name": vendor.business_name,
            "market_id": vendor.market_id,
            "market_name": market_name,
            "is_verified": vendor.is_verified,
            "average_rating": vendor.average_rating,
            "total_reviews": vendor.total_reviews,
            "specialties": vendor.specialties
        }
        result.append(VendorListResponse(**vendor_dict))
    
    return result

@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    """Get a specific vendor by ID."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Get related data
    user = db.query(User).filter(User.id == vendor.user_id).first()
    market = db.query(Market).filter(Market.id == vendor.market_id).first()
    product_count = db.query(Product).filter(Product.vendor_id == vendor_id).count()
    
    # Build response
    vendor_dict = vendor.__dict__.copy()
    vendor_dict["user"] = user
    vendor_dict["market_name"] = market.name if market else None
    vendor_dict["product_count"] = product_count
    
    return VendorResponse(**vendor_dict)

@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor_profile(
    vendor_data: VendorCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create vendor profile (user must have vendor role)."""
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users with vendor role can create vendor profiles"
        )
    
    # Check if user already has a vendor profile
    existing_vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()
    if existing_vendor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a vendor profile"
        )
    
    # Verify market exists
    market = db.query(Market).filter(Market.id == vendor_data.market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Create vendor profile
    db_vendor = Vendor(
        user_id=current_user.id,
        **vendor_data.dict()
    )
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
    # Build response
    vendor_dict = db_vendor.__dict__.copy()
    vendor_dict["user"] = current_user
    vendor_dict["market_name"] = market.name
    vendor_dict["product_count"] = 0
    
    return VendorResponse(**vendor_dict)

@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    vendor_data: VendorUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update vendor profile."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and vendor.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this vendor profile"
        )
    
    # Verify new market exists if being changed
    if vendor_data.market_id and vendor_data.market_id != vendor.market_id:
        market = db.query(Market).filter(Market.id == vendor_data.market_id).first()
        if not market:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New market not found"
            )
    
    # Update vendor data
    update_data = vendor_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)
    
    db.commit()
    db.refresh(vendor)
    
    # Get related data for response
    user = db.query(User).filter(User.id == vendor.user_id).first()
    market = db.query(Market).filter(Market.id == vendor.market_id).first()
    product_count = db.query(Product).filter(Product.vendor_id == vendor_id).count()
    
    vendor_dict = vendor.__dict__.copy()
    vendor_dict["user"] = user
    vendor_dict["market_name"] = market.name if market else None
    vendor_dict["product_count"] = product_count
    
    return VendorResponse(**vendor_dict)

@router.get("/me/profile", response_model=VendorResponse)
def get_my_vendor_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's vendor profile."""
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a vendor"
        )
    
    vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor profile not found"
        )
    
    # Get related data
    market = db.query(Market).filter(Market.id == vendor.market_id).first()
    product_count = db.query(Product).filter(Product.vendor_id == vendor.id).count()
    
    vendor_dict = vendor.__dict__.copy()
    vendor_dict["user"] = current_user
    vendor_dict["market_name"] = market.name if market else None
    vendor_dict["product_count"] = product_count
    
    return VendorResponse(**vendor_dict)

@router.post("/{vendor_id}/verify")
def verify_vendor(
    vendor_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Verify a vendor (admin only)."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    vendor.is_verified = True
    db.commit()
    
    return {"message": "Vendor verified successfully"}

@router.post("/{vendor_id}/unverify")
def unverify_vendor(
    vendor_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Remove vendor verification (admin only)."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    vendor.is_verified = False
    db.commit()
    
    return {"message": "Vendor verification removed"}

@router.get("/market/{market_id}/vendors", response_model=List[VendorListResponse])
def get_vendors_by_market(
    market_id: int,
    verified_only: bool = Query(False, description="Show only verified vendors"),
    db: Session = Depends(get_db)
):
    """Get all vendors in a specific market."""
    # Verify market exists
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    query = db.query(Vendor).filter(Vendor.market_id == market_id)
    
    if verified_only:
        query = query.filter(Vendor.is_verified == True)
    
    vendors = query.all()
    
    # Format response
    result = []
    for vendor in vendors:
        vendor_dict = {
            "id": vendor.id,
            "business_name": vendor.business_name,
            "market_id": vendor.market_id,
            "market_name": market.name,
            "is_verified": vendor.is_verified,
            "average_rating": vendor.average_rating,
            "total_reviews": vendor.total_reviews,
            "specialties": vendor.specialties
        }
        result.append(VendorListResponse(**vendor_dict))
    
    return result