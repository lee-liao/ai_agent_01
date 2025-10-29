"""
Media upload API for edge devices
Allows uploading images and videos for truck records
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
from pathlib import Path
import uuid
from datetime import datetime

from ..database import get_db
from ..models import Truck

router = APIRouter(prefix="/api/media", tags=["Media Upload"])

# Create uploads directory structure
UPLOAD_BASE = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIRS = {
    "images": UPLOAD_BASE / "images",
    "videos": UPLOAD_BASE / "videos",
    "thumbnails": UPLOAD_BASE / "thumbnails"
}

# Create directories if they don't exist
for directory in UPLOAD_DIRS.values():
    directory.mkdir(parents=True, exist_ok=True)


def save_file(file: UploadFile, file_type: str, truck_id: int) -> str:
    """Save uploaded file and return the filename"""
    # Get file extension
    ext = Path(file.filename).suffix if file.filename else ""
    
    # Generate unique filename: truckID_timestamp_uuid.ext
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"truck_{truck_id}_{timestamp}_{unique_id}{ext}"
    
    # Save file
    file_path = UPLOAD_DIRS[file_type] / filename
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    return filename


@router.post("/upload")
async def upload_truck_media(
    truck_id: int = Form(...),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Upload image and/or video for a truck record.
    
    **Parameters:**
    - `truck_id`: The ID returned from POST /api/truck-count
    - `image`: Image file (JPG, PNG, etc.)
    - `video`: Video file (MP4, AVI, etc.) - optional
    
    **Returns:**
    - Updated truck record with file paths
    
    **Example using curl:**
    ```bash
    curl -X POST http://localhost:8095/api/media/upload \\
      -F "truck_id=1744" \\
      -F "image=@/path/to/truck_image.jpg" \\
      -F "video=@/path/to/truck_video.mp4"
    ```
    
    **Example using Python:**
    ```python
    import requests
    
    # First post truck data
    response = requests.post("http://localhost:8095/api/truck-count", json={...})
    truck_id = response.json()['truck_id']
    
    # Then upload media
    files = {
        'image': open('truck.jpg', 'rb'),
        'video': open('truck.mp4', 'rb')  # optional
    }
    data = {'truck_id': truck_id}
    requests.post("http://localhost:8095/api/media/upload", files=files, data=data)
    ```
    """
    try:
        # Get truck record
        truck = db.query(Truck).filter(Truck.id == truck_id).first()
        if not truck:
            raise HTTPException(status_code=404, detail=f"Truck ID {truck_id} not found")
        
        uploaded_files = {}
        
        # Process image
        if image and image.filename:
            image_filename = save_file(image, "images", truck_id)
            truck.image_url = f"/uploads/images/{image_filename}"
            uploaded_files['image'] = image_filename
            
            # Also create a thumbnail copy (in production, you'd resize it)
            truck.thumbnail_url = f"/uploads/thumbnails/{image_filename}"
        
        # Process video
        if video and video.filename:
            video_filename = save_file(video, "videos", truck_id)
            truck.video_url = f"/uploads/videos/{video_filename}"
            uploaded_files['video'] = video_filename
        
        # Update database
        db.commit()
        db.refresh(truck)
        
        return {
            "status": "success",
            "message": "Media uploaded successfully",
            "truck_id": truck_id,
            "uploaded_files": uploaded_files,
            "truck": {
                "id": truck.id,
                "truck_number": truck.truck_number,
                "image_url": truck.image_url,
                "video_url": truck.video_url,
                "thumbnail_url": truck.thumbnail_url
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading media: {str(e)}")


@router.get("/uploads/{file_type}/{filename}")
async def get_media_file(file_type: str, filename: str):
    """
    Serve uploaded media files
    
    **Parameters:**
    - `file_type`: Type of file (images, videos, thumbnails)
    - `filename`: Name of the file
    """
    from fastapi.responses import FileResponse
    
    if file_type not in UPLOAD_DIRS:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = UPLOAD_DIRS[file_type] / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)


@router.delete("/truck/{truck_id}/media")
async def delete_truck_media(
    truck_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete all media files associated with a truck record
    
    **Parameters:**
    - `truck_id`: The truck ID
    """
    try:
        truck = db.query(Truck).filter(Truck.id == truck_id).first()
        if not truck:
            raise HTTPException(status_code=404, detail=f"Truck ID {truck_id} not found")
        
        deleted_files = []
        
        # Delete image
        if truck.image_url:
            filename = Path(truck.image_url).name
            image_path = UPLOAD_DIRS["images"] / filename
            if image_path.exists():
                image_path.unlink()
                deleted_files.append(f"image: {filename}")
        
        # Delete video
        if truck.video_url:
            filename = Path(truck.video_url).name
            video_path = UPLOAD_DIRS["videos"] / filename
            if video_path.exists():
                video_path.unlink()
                deleted_files.append(f"video: {filename}")
        
        # Delete thumbnail
        if truck.thumbnail_url:
            filename = Path(truck.thumbnail_url).name
            thumb_path = UPLOAD_DIRS["thumbnails"] / filename
            if thumb_path.exists():
                thumb_path.unlink()
                deleted_files.append(f"thumbnail: {filename}")
        
        # Update database
        truck.image_url = None
        truck.video_url = None
        truck.thumbnail_url = None
        db.commit()
        
        return {
            "status": "success",
            "message": "Media deleted successfully",
            "truck_id": truck_id,
            "deleted_files": deleted_files
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting media: {str(e)}")






