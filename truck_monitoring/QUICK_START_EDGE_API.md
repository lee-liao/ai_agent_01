# 🚀 Edge API Quick Start

## One-Command Test

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

Expected response:
```json
{
  "status": "success",
  "message": "Truck recorded successfully: Flatbed",
  "truck_id": 1744,
  "timestamp": "2025-10-16T14:30:45"
}
```

## Python Test Script

```bash
cd backend
python3 test_edge_api.py
```

## Important URLs

- **Edge API:** http://localhost:8095/api/truck-count
- **API Docs:** http://localhost:8095/docs
- **Health Check:** http://localhost:8095/health

## Direction Codes

| Code | Direction |
|------|-----------|
| 0 | Unknown |
| 1 | Northbound |
| 2 | Southbound |
| 3 | Eastbound |
| 4 | Westbound |

## Minimum Required Fields

```json
{
  "id": 1,
  "timestamp": "2025-10-16T14:30:45",
  "length_mm": 8500,
  "height_mm": 2800,
  "is_truck": true,
  "classification_confidence": 0.87,
  "image_path": "test.jpg"
}
```

## Quick Python Example

```python
import requests
from datetime import datetime

requests.post("http://localhost:8095/api/truck-count", json={
    "id": 1,
    "timestamp": datetime.now().isoformat(),
    "length_mm": 10000,
    "height_mm": 3000,
    "is_truck": True,
    "classification_confidence": 0.85,
    "image_path": "truck.jpg",
    "video_path": "",
    "direction": 1,
    "speed_kmh": 65.0
}).json()
```

## Features

✅ No authentication required  
✅ Auto-classifies truck types  
✅ Filters low confidence (<0.5)  
✅ Updates daily statistics  
✅ Records all truck data  

## For More Details

See `EDGE_API_GUIDE.md` for complete documentation.






