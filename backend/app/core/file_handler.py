import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import aiofiles

# Configuration
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
IMAGE_SIZES = {
    "thumbnail": (150, 150),
    "medium": (400, 400),
    "large": (800, 800)
}

def create_upload_dirs():
    """Create upload directories if they don't exist."""
    for subdir in ["markets", "products", "profiles", "temp"]:
        (UPLOAD_DIR / subdir).mkdir(parents=True, exist_ok=True)

def generate_filename(original_filename: str) -> str:
    """Generate a unique filename."""
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4()}{ext}"

def validate_image_file(file: UploadFile) -> bool:
    """Validate if file is a valid image."""
    if not file.content_type or not file.content_type.startswith("image/"):
        return False
    
    ext = Path(file.filename or "").suffix.lower()
    return ext in ALLOWED_EXTENSIONS

async def save_image(file: UploadFile, subdir: str) -> Optional[str]:
    """Save uploaded image and return filename."""
    if not validate_image_file(file):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Generate filename and path
    filename = generate_filename(file.filename or "image")
    file_path = UPLOAD_DIR / subdir / filename
    
    try:
        # Save original file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create thumbnail
        create_thumbnail(file_path)
        
        return filename
    except Exception as e:
        # Clean up if something went wrong
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

def create_thumbnail(image_path: Path) -> None:
    """Create thumbnail version of image."""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Create thumbnail
            img.thumbnail(IMAGE_SIZES["thumbnail"], Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumbnail_path = image_path.parent / f"thumb_{image_path.name}"
            img.save(thumbnail_path, quality=85, optimize=True)
    except Exception as e:
        print(f"Failed to create thumbnail: {e}")

def delete_image(filename: str, subdir: str) -> bool:
    """Delete image and its thumbnail."""
    try:
        file_path = UPLOAD_DIR / subdir / filename
        thumb_path = UPLOAD_DIR / subdir / f"thumb_{filename}"
        
        if file_path.exists():
            file_path.unlink()
        if thumb_path.exists():
            thumb_path.unlink()
        
        return True
    except Exception:
        return False

# Initialize upload directories
create_upload_dirs()