"""
Edge computer API routes for truck detection
These endpoints do NOT require authentication
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models import Truck, DailyStatistics

router = APIRouter(prefix="/api", tags=["Edge"])


class EdgeTruckData(BaseModel):
    """Data format from edge computer"""
    id: int
    timestamp: str
    length_mm: int
    height_mm: int
    is_truck: bool
    classification_confidence: float
    image_path: str
    video_path: Optional[str] = ""
    direction: int = 0  # 0=unknown, 1=north, 2=south, 3=east, 4=west
    speed_kmh: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "timestamp": "2025-10-16T14:30:45",
                "length_mm": 8500,
                "height_mm": 2800,
                "is_truck": True,
                "classification_confidence": 0.87,
                "image_path": "test.jpg",
                "video_path": "",
                "direction": 0,
                "speed_kmh": 0.0
            }
        }


class EdgeTruckResponse(BaseModel):
    """Response for edge truck submission"""
    status: str
    message: str
    truck_id: int
    timestamp: str


def update_daily_statistics(db: Session, truck: Truck):
    """Update daily statistics after adding a new truck"""
    date_str = truck.date
    
    # Get or create daily statistics
    stats = db.query(DailyStatistics).filter(DailyStatistics.date == date_str).first()
    
    if not stats:
        stats = DailyStatistics(
            date=date_str,
            total_trucks=0,
            avg_length=0.0,
            avg_speed=0.0,
            container_count=0,
            flatbed_count=0,
            tanker_count=0,
            other_count=0,
            peak_hour=0,
            peak_hour_count=0
        )
        db.add(stats)
    
    # Get all trucks for this date
    all_trucks = db.query(Truck).filter(Truck.date == date_str).all()
    
    # Update statistics
    stats.total_trucks = len(all_trucks)
    
    # Calculate averages
    lengths = [t.length_meters for t in all_trucks if t.length_meters]
    speeds = [t.speed_kmh for t in all_trucks if t.speed_kmh]
    
    stats.avg_length = sum(lengths) / len(lengths) if lengths else 0.0
    stats.avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
    
    # Count by type
    type_counts = {"Container": 0, "Flatbed": 0, "Tanker": 0, "Box Truck": 0, "Small Truck": 0, "Other": 0}
    for t in all_trucks:
        truck_type = t.truck_type or "Other"
        if truck_type in type_counts:
            type_counts[truck_type] += 1
        else:
            type_counts["Other"] += 1
    
    stats.container_count = type_counts.get("Container", 0)
    stats.flatbed_count = type_counts.get("Flatbed", 0)
    stats.tanker_count = type_counts.get("Tanker", 0)
    stats.other_count = type_counts.get("Box Truck", 0) + type_counts.get("Small Truck", 0) + type_counts.get("Other", 0)
    
    # Find peak hour
    hour_counts = {}
    for t in all_trucks:
        hour = t.pass_time.hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    if hour_counts:
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])
        stats.peak_hour = peak_hour[0]
        stats.peak_hour_count = peak_hour[1]
    
    db.commit()


@router.post("/truck-count", response_model=EdgeTruckResponse)
async def receive_truck_from_edge(
    data: EdgeTruckData,
    db: Session = Depends(get_db)
):
    """
    Receive truck detection data from edge computer.
    This endpoint does NOT require authentication.
    
    Direction mapping:
    - 0: Unknown
    - 1: Northbound
    - 2: Southbound
    - 3: Eastbound
    - 4: Westbound
    
    Example usage:
    ```bash
    curl -X POST http://localhost:8095/api/truck-count \
      -H "Content-Type: application/json" \
      -d '{
        "id": 1,
        "timestamp": "2025-10-16T14:30:45",
        "length_mm": 8500,
        "height_mm": 2800,
        "is_truck": true,
        "classification_confidence": 0.87,
        "image_path": "test.jpg",
        "video_path": "",
        "direction": 0,
        "speed_kmh": 0.0
      }'
    ```
    """
    try:
        # Skip if not classified as a truck
        if not data.is_truck:
            return EdgeTruckResponse(
                status="skipped",
                message="Not classified as a truck",
                truck_id=0,
                timestamp=data.timestamp
            )
        
        # Skip if confidence too low (optional threshold)
        if data.classification_confidence < 0.5:
            return EdgeTruckResponse(
                status="skipped",
                message=f"Confidence too low: {data.classification_confidence}",
                truck_id=0,
                timestamp=data.timestamp
            )
        
        # Parse timestamp
        try:
            pass_time = datetime.fromisoformat(data.timestamp.replace('Z', '+00:00'))
        except:
            pass_time = datetime.now()
        
        # Map direction
        direction_map = {
            0: "Unknown",
            1: "Northbound",
            2: "Southbound",
            3: "Eastbound",
            4: "Westbound"
        }
        direction_str = direction_map.get(data.direction, "Unknown")
        
        # Convert length from mm to meters
        length_meters = data.length_mm / 1000.0
        
        # Classify truck type based on length
        if length_meters >= 12.0:
            truck_type = "Container"
        elif length_meters >= 8.0:
            truck_type = "Flatbed"
        elif length_meters >= 6.0:
            truck_type = "Box Truck"
        else:
            truck_type = "Small Truck"
        
        # Create truck record
        new_truck = Truck(
            truck_number=f"EDGE-{data.id}-{pass_time.strftime('%Y%m%d%H%M%S')}",
            license_plate=None,  # Edge computer doesn't provide this
            truck_type=truck_type,
            length_meters=length_meters,
            weight_tons=None,  # Not provided by edge
            speed_kmh=data.speed_kmh if data.speed_kmh > 0 else None,
            location="Edge Detection Point",
            direction=direction_str,
            pass_time=pass_time,
            date=pass_time.strftime("%Y-%m-%d"),
            image_url=f"/uploads/images/{data.image_path}" if data.image_path else None,
            video_url=f"/uploads/videos/{data.video_path}" if data.video_path else None,
            thumbnail_url=f"/uploads/thumbnails/{data.image_path}" if data.image_path else None,
            company_name=None,
            driver_name=None,
            cargo_description=None,
            notes=f"Edge detection | Confidence: {data.classification_confidence:.2%} | Height: {data.height_mm}mm"
        )
        
        db.add(new_truck)
        db.commit()
        db.refresh(new_truck)
        
        # Update daily statistics
        update_daily_statistics(db, new_truck)
        
        return EdgeTruckResponse(
            status="success",
            message=f"Truck recorded successfully: {truck_type}",
            truck_id=new_truck.id,
            timestamp=data.timestamp
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing truck data: {str(e)}"
        )






