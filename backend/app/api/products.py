from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from app.database import get_db
from app.models.product import Product, Category
from app.models.vendor import Vendor
from app.models.market import Market
from app.models.user import User, UserRole
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from app.core.dependencies import get_current_active_user, require_vendor_or_admin
from app.core.file_handler import save_image, delete_image

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=List[ProductListResponse])
def get_products(
    skip: int = Query(0, description="Number of products to skip"),
    limit: int = Query(100, description="Maximum number of products to return"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    market_id: Optional[int] = Query(None, description="Filter by market ID"),
    is_organic: Optional[bool] = Query(None, description="Filter organic products"),
    available_only: bool = Query(True, description="Show only available products"),
    search: Optional[str] = Query(None, description="Search in product names and descriptions"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    db: Session = Depends(get_db)
):
    """Get list of products with optional filters."""
    query = db.query(
        Product,
        Vendor.business_name.label("vendor_name"),
        Market.name.label("market_name"),
        Category.name.label("category_name")
    ).join(Vendor, Product.vendor_id == Vendor.id)\
     .join(Market, Vendor.market_id == Market.id)\
     .join(Category, Product.category_id == Category.id)
    
    # Apply filters
    if available_only:
        query = query.filter(Product.is_available == True)
    if vendor_id:
        query = query.filter(Product.vendor_id == vendor_id)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if market_id:
        query = query.filter(Vendor.market_id == market_id)
    if is_organic is not None:
        query = query.filter(Product.is_organic == is_organic)
    if min_price:
        query = query.filter(Product.price_per_unit >= min_price)
    if max_price:
        query = query.filter(Product.price_per_unit <= max_price)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.name_ja.ilike(search_term),
                Product.name_ne.ilike(search_term)
            )
        )
    
    products = query.offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for product, vendor_name, market_name, category_name in products:
        product_dict = {
            "id": product.id,
            "name": product.name,
            "price_per_unit": product.price_per_unit,
            "unit": product.unit,
            "vendor_id": product.vendor_id,
            "vendor_name": vendor_name,
            "market_name": market_name,
            "category_name": category_name,
            "is_available": product.is_available,
            "is_organic": product.is_organic,
            "main_image": product.main_image,
            "stock_quantity": product.stock_quantity
        }
        result.append(ProductListResponse(**product_dict))
    
    return result

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get related data
    category = db.query(Category).filter(Category.id == product.category_id).first()
    vendor = db.query(Vendor).filter(Vendor.id == product.vendor_id).first()
    market = db.query(Market).filter(Market.id == vendor.market_id).first() if vendor else None
    
    # Build response
    product_dict = product.__dict__.copy()
    product_dict["category"] = category
    product_dict["vendor_name"] = vendor.business_name if vendor else None
    product_dict["market_name"] = market.name if market else None
    
    return ProductResponse(**product_dict)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new product (vendor only)."""
    # Get vendor profile
    vendor = None
    if current_user.role == UserRole.VENDOR:
        vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor profile not found"
            )
    elif current_user.role == UserRole.ADMIN:
        # Admin can create products for any vendor (for testing/management)
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can create products"
        )
    
    # Verify category exists
    category = db.query(Category).filter(Category.id == product_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Create product
    product_dict = product_data.dict()
    if vendor:
        product_dict["vendor_id"] = vendor.id
    
    db_product = Product(**product_dict)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Get related data for response
    if not vendor:
        vendor = db.query(Vendor).filter(Vendor.id == db_product.vendor_id).first()
    market = db.query(Market).filter(Market.id == vendor.market_id).first() if vendor else None
    
    # Build response
    product_dict = db_product.__dict__.copy()
    product_dict["category"] = category
    product_dict["vendor_name"] = vendor.business_name if vendor else None
    product_dict["market_name"] = market.name if market else None
    
    return ProductResponse(**product_dict)

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.VENDOR:
        vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()
        if not vendor or product.vendor_id != vendor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this product"
            )
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update products"
        )
    
    # Verify new category exists if being changed
    if product_data.category_id and product_data.category_id != product.category_id:
        category = db.query(Category).filter(Category.id == product_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New category not found"
            )
    
    # Update product data
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # Get related data for response
    category = db.query(Category).filter(Category.id == product.category_id).first()
    vendor = db.query(Vendor).filter(Vendor.id == product.vendor_id).first()
    market = db.query(Market).filter(Market.id == vendor.market_id).first() if vendor else None
    
    product_dict = product.__dict__.copy()
    product_dict["category"] = category
    product_dict["vendor_name"] = vendor.business_name if vendor else None
    product_dict["market_name"] = market.name if market else None
    
    return ProductResponse(**product_dict)

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.VENDOR:
        vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()
        if not vendor or product.vendor_id != vendor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this product"
            )
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete products"
        )
    
    # Delete product images if they exist
    if product.main_image:
        delete_image(product.main_image, "products")
    
    db.delete(product)
    db.commit()
    
    return {"message": "Product deleted successfully"}

@router.post("/{product_id}/upload-image")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload product image."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.VENDOR:
        vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()
        if not vendor or product.vendor_id != vendor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this product"
            )
    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update products"
        )
    
    # Save the image
    filename = await save_image(file, "products")
    
    # Delete old image if exists
    if product.main_image:
        delete_image(product.main_image, "products")
    
    # Update product with new image
    product.main_image = filename
    db.commit()
    
    return {"message": "Image uploaded successfully", "filename": filename}

@router.get("/vendor/{vendor_id}/products", response_model=List[ProductListResponse])
def get_vendor_products(
    vendor_id: int,
    available_only: bool = Query(True, description="Show only available products"),
    db: Session = Depends(get_db)
):
    """Get all products for a specific vendor."""
    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    query = db.query(
        Product,
        Category.name.label("category_name")
    ).join(Category, Product.category_id == Category.id)\
     .filter(Product.vendor_id == vendor_id)
    
    if available_only:
        query = query.filter(Product.is_available == True)
    
    products = query.all()
    
    # Get market info
    market = db.query(Market).filter(Market.id == vendor.market_id).first()
    
    # Format response
    result = []
    for product, category_name in products:
        product_dict = {
            "id": product.id,
            "name": product.name,
            "price_per_unit": product.price_per_unit,
            "unit": product.unit,
            "vendor_id": product.vendor_id,
            "vendor_name": vendor.business_name,
            "market_name": market.name if market else None,
            "category_name": category_name,
            "is_available": product.is_available,
            "is_organic": product.is_organic,
            "main_image": product.main_image,
            "stock_quantity": product.stock_quantity
        }
        result.append(ProductListResponse(**product_dict))
    
    return result

@router.get("/my/products", response_model=List[ProductListResponse])
def get_my_products(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current vendor's products."""
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can access this endpoint"
        )
    
    vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor profile not found"
        )
    
    return get_vendor_products(vendor.id, available_only=False, db=db)

@router.get("/search/suggestions")
def get_product_search_suggestions(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of suggestions"),
    db: Session = Depends(get_db)
):
    """Get product search suggestions."""
    search_term = f"%{q}%"
    suggestions = db.query(Product.name).filter(
        Product.is_available == True,
        or_(
            Product.name.ilike(search_term),
            Product.name_ja.ilike(search_term),
            Product.name_ne.ilike(search_term)
        )
    ).distinct().limit(limit).all()
    
    return [{"name": name} for name, in suggestions]