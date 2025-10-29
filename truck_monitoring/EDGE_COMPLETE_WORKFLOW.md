# 🚛 Edge Device - Complete Workflow Reference

## Quick Summary

Your edge computer now has **2 APIs** to interact with the server:

1. **POST /api/truck-count** - Send truck detection data
2. **POST /api/media/upload** - Upload images and videos

---

## 📋 Two-Step Process

### Step 1: Detect and Post Truck Data

```bash
curl -X POST http://localhost:8095/api/truck-count \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "timestamp": "2025-10-16T14:30:45",
    "length_mm": 12500,
    "height_mm": 3400,
    "is_truck": true,
    "classification_confidence": 0.94,
    "image_path": "truck_001.jpg",
    "video_path": "truck_001.mp4",
    "direction": 1,
    "speed_kmh": 68.5
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Truck recorded successfully: Container",
  "truck_id": 1753,
  "timestamp": "2025-10-16T14:30:45"
}
```

✅ **Save the `truck_id`!**

---

### Step 2: Upload Image and Video

```bash
curl -X POST http://localhost:8095/api/media/upload \
  -F "truck_id=1753" \
  -F "image=@/path/to/truck_image.jpg" \
  -F "video=@/path/to/truck_video.mp4"
```

**Response:**
```json
{
  "status": "success",
  "message": "Media uploaded successfully",
  "truck_id": 1753,
  "uploaded_files": {
    "image": "truck_1753_20251016_125514_95d0f6bc.jpg",
    "video": "truck_1753_20251016_125514_847945a0.mp4"
  },
  "truck": {
    "image_url": "/uploads/images/truck_1753_20251016_125514_95d0f6bc.jpg",
    "video_url": "/uploads/videos/truck_1753_20251016_125514_847945a0.mp4"
  }
}
```

---

## 🐍 Python Example

```python
import requests
from datetime import datetime

# Step 1: Post truck detection
truck_data = {
    "id": 1,
    "timestamp": datetime.now().isoformat(),
    "length_mm": 12500,
    "height_mm": 3400,
    "is_truck": True,
    "classification_confidence": 0.94,
    "image_path": "truck_001.jpg",
    "video_path": "truck_001.mp4",
    "direction": 1,
    "speed_kmh": 68.5
}

response = requests.post("http://localhost:8095/api/truck-count", json=truck_data)
truck_id = response.json()['truck_id']
print(f"✅ Truck ID: {truck_id}")

# Step 2: Upload media
files = {
    'image': open('/path/to/truck_image.jpg', 'rb'),
    'video': open('/path/to/truck_video.mp4', 'rb')
}
data = {'truck_id': truck_id}

response = requests.post("http://localhost:8095/api/media/upload", files=files, data=data)
print(f"✅ Media uploaded: {response.json()['message']}")

# Close files
for f in files.values():
    f.close()
```

---

## 📱 Raspberry Pi Example

```python
#!/usr/bin/env python3
import requests
from datetime import datetime
from picamera2 import Picamera2
import io

API_URL = "http://your-server:8095"
camera = Picamera2()
camera.start()

def process_truck(detection_id, truck_length_mm, confidence):
    """Complete workflow: detect, post, upload"""
    
    # Capture image
    image_stream = io.BytesIO()
    camera.capture_file(image_stream, format='jpeg')
    image_stream.seek(0)
    
    # Step 1: Post detection
    truck_data = {
        "id": detection_id,
        "timestamp": datetime.now().isoformat(),
        "length_mm": truck_length_mm,
        "height_mm": 3000,
        "is_truck": True,
        "classification_confidence": confidence,
        "image_path": f"truck_{detection_id}.jpg",
        "video_path": "",
        "direction": 1,
        "speed_kmh": 65.0
    }
    
    response = requests.post(f"{API_URL}/api/truck-count", json=truck_data)
    truck_id = response.json()['truck_id']
    
    # Step 2: Upload image
    files = {'image': ('truck.jpg', image_stream, 'image/jpeg')}
    data = {'truck_id': truck_id}
    
    requests.post(f"{API_URL}/api/media/upload", files=files, data=data)
    
    print(f"✅ Processed truck {truck_id}")
    return truck_id

# Use in your detection loop
if truck_detected:
    process_truck(
        detection_id=1,
        truck_length_mm=12000,
        confidence=0.92
    )
```

---

## 🧪 Test Script

Run the provided test script:

```bash
cd backend
python3 test_edge_with_media.py
```

---

## 🔍 Verify Upload

### Check in Web UI

1. Open http://localhost:3000
2. Login with `admin` / `admin123`
3. View recent trucks
4. Images and videos should display!

### Check via API

```bash
# Get truck details
curl http://localhost:8095/api/trucks/1753 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Access image directly
curl http://localhost:8095/uploads/images/truck_1753_*.jpg
```

### Check files on disk

```bash
ls -lh backend/uploads/images/
ls -lh backend/uploads/videos/
```

---

## 🎯 Quick Reference

| Action | Endpoint | Method | Auth Required |
|--------|----------|--------|---------------|
| Post truck detection | `/api/truck-count` | POST | No |
| Upload media | `/api/media/upload` | POST | No |
| Get truck details | `/api/trucks/{id}` | GET | Yes |
| Access image | `/uploads/images/{file}` | GET | No |
| Access video | `/uploads/videos/{file}` | GET | No |

---

## 📊 Direction Codes

| Code | Direction |
|------|-----------|
| 0 | Unknown |
| 1 | Northbound |
| 2 | Southbound |
| 3 | Eastbound |
| 4 | Westbound |

---

## ⚠️ Important Notes

### 1. Two Steps Required

You **must** post truck detection first to get the `truck_id`, then upload media.

### 2. Video is Optional

You can upload just an image:
```bash
curl -X POST http://localhost:8095/api/media/upload \
  -F "truck_id=1753" \
  -F "image=@truck.jpg"
```

### 3. Unique Filenames

Files are automatically renamed to:
```
truck_{truck_id}_{timestamp}_{uuid}.{ext}
```

Example: `truck_1753_20251016_125514_95d0f6bc.jpg`

### 4. No Authentication

Both endpoints work without authentication (designed for edge devices in trusted networks).

---

## 🐛 Troubleshooting

### "Truck ID not found"

You must post truck detection (Step 1) **before** uploading media (Step 2).

### "No file uploaded"

Include at least one file:
```bash
-F "image=@file.jpg"  # or
-F "video=@file.mp4"  # or both
```

### Files not showing in UI

1. Check files uploaded: `ls backend/uploads/images/`
2. Refresh the web UI page
3. Check browser console for errors
4. Verify truck record has image_url: `GET /api/trucks/{id}`

---

## 📖 Complete Documentation

- **Media Upload Guide:** [MEDIA_UPLOAD_GUIDE.md](MEDIA_UPLOAD_GUIDE.md)
- **Edge API Guide:** [EDGE_API_GUIDE.md](EDGE_API_GUIDE.md)
- **Quick Start:** [QUICK_START_EDGE_API.md](QUICK_START_EDGE_API.md)
- **Main README:** [README.md](README.md)
- **API Docs:** http://localhost:8095/docs

---

## 🚀 Ready to Use!

Your system is now fully functional with:

✅ Truck detection posting  
✅ Image/video upload  
✅ Web UI display  
✅ Database storage  
✅ File serving  

**Start sending data from your edge devices!** 🎉






