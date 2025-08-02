from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.models.market import Market
from app.models.vendor import Vendor
from app.models.user import User
from app.schemas.market import MarketCreate, MarketUpdate, MarketResponse, MarketListResponse
from app.core.dependencies import require_admin, get_current_active_user
from app.core.file_handler import save_image, delete_image

router = APIRouter(prefix="/markets", tags=["Markets"])

@router.get("/", response_model=List[MarketListResponse])
def get_markets(
    skip: int = Query(0, description="Number of markets to skip"),
    limit: int = Query(100, description="Maximum number of markets to return"),
    city: Optional[str] = Query(None, description="Filter by city"),
    prefecture: Optional[str] = Query(None, description="Filter by prefecture"),
    market_type: Optional[str] = Query(None, description="Filter by market type"),
    active_only: bool = Query(True, description="Show only active markets"),
    db: Session = Depends(get_db)
):
    """Get list of markets with optional filters."""
    query = db.query(
        Market,
        func.count(Vendor.id).label("vendor_count")
    ).outerjoin(Vendor, Market.id == Vendor.market_id)
    
    # Apply filters
    if active_only:
        query = query.filter(Market.is_active == True)
    if city:
        query = query.filter(Market.city.ilike(f"%{city}%"))
    if prefecture:
        query = query.filter(Market.prefecture.ilike(f"%{prefecture}%"))
    if market_type:
        query = query.filter(Market.market_type == market_type)
    
    # Group by market and apply pagination
    markets = query.group_by(Market.id).offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for market, vendor_count in markets:
        market_dict = {
            "id": market.id,
            "name": market.name,
            "city": market.city,
            "prefecture": market.prefecture,
            "market_type": market.market_type,
            "main_image": market.main_image,
            "is_active": market.is_active,
            "vendor_count": vendor_count or 0,
            "latitude": market.latitude,
            "longitude": market.longitude
        }
        result.append(MarketListResponse(**market_dict))
    
    return result

@router.get("/{market_id}", response_model=MarketResponse)
def get_market(market_id: int, db: Session = Depends(get_db)):
    """Get a specific market by ID."""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Get vendor count
    vendor_count = db.query(Vendor).filter(Vendor.market_id == market_id).count()
    
    # Add vendor count to response
    market_dict = market.__dict__.copy()
    market_dict["vendor_count"] = vendor_count
    
    return MarketResponse(**market_dict)

@router.post("/", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
def create_market(
    market_data: MarketCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new market (admin only)."""
    # Check if market with same name already exists in the city
    existing_market = db.query(Market).filter(
        Market.name == market_data.name,
        Market.city == market_data.city
    ).first()
    
    if existing_market:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market with this name already exists in this city"
        )
    
    # Create new market
    db_market = Market(**market_data.dict())
    db.add(db_market)
    db.commit()
    db.refresh(db_market)
    
    # Add vendor count
    market_dict = db_market.__dict__.copy()
    market_dict["vendor_count"] = 0
    
    return MarketResponse(**market_dict)

@router.put("/{market_id}", response_model=MarketResponse)
def update_market(
    market_id: int,
    market_data: MarketUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a market (admin only)."""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Update market data
    update_data = market_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(market, field, value)
    
    db.commit()
    db.refresh(market)
    
    # Get vendor count
    vendor_count = db.query(Vendor).filter(Vendor.market_id == market_id).count()
    market_dict = market.__dict__.copy()
    market_dict["vendor_count"] = vendor_count
    
    return MarketResponse(**market_dict)

@router.delete("/{market_id}")
def delete_market(
    market_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Soft delete a market (admin only)."""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Check if market has active vendors
    active_vendors = db.query(Vendor).filter(Vendor.market_id == market_id).count()
    if active_vendors > 0:
        # Soft delete - just deactivate
        market.is_active = False
        db.commit()
        return {"message": "Market deactivated successfully"}
    else:
        # Hard delete if no vendors
        db.delete(market)
        db.commit()
        return {"message": "Market deleted successfully"}

@router.post("/{market_id}/upload-image")
def upload_market_image(
    market_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Upload market image (admin only)."""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    # Save the image
    filename = save_image(file, "markets")
    
    # Delete old image if exists
    if market.main_image:
        delete_image(market.main_image, "markets")
    
    # Update market with new image
    market.main_image = filename
    db.commit()
    
    return {"message": "Image uploaded successfully", "filename": filename}

@router.get("/search/suggestions")
def get_market_suggestions(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Maximum number of suggestions"),
    db: Session = Depends(get_db)
):
    """Get market search suggestions."""
    suggestions = db.query(Market.name, Market.city, Market.prefecture).filter(
        Market.is_active == True,
        Market.name.ilike(f"%{q}%")
    ).distinct().limit(limit).all()
    
    return [
        {"name": name, "city": city, "prefecture": prefecture}
        for name, city, prefecture in suggestions
    ]