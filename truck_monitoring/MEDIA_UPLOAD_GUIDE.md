# 📸 Media Upload API Guide

## Overview

The Media Upload API allows edge computers to upload images and videos for their truck detections. This is a **two-step process**:

1. **Post truck detection data** → Get `truck_id`
2. **Upload media files** → Associate with `truck_id`

---

## 🚀 Complete Workflow

### Step 1: Post Truck Detection

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

**Save the `truck_id`!** You'll need it for step 2.

---

### Step 2: Upload Media Files

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
    "id": 1753,
    "truck_number": "EDGE-2001-20251016143045",
    "image_url": "/uploads/images/truck_1753_20251016_125514_95d0f6bc.jpg",
    "video_url": "/uploads/videos/truck_1753_20251016_125514_847945a0.mp4",
    "thumbnail_url": "/uploads/thumbnails/truck_1753_20251016_125514_95d0f6bc.jpg"
  }
}
```

---

## 📋 API Endpoints

### POST `/api/media/upload`

Upload image and/or video for a truck record.

**Parameters:**
- `truck_id` (Form data, required): The truck ID from step 1
- `image` (File, optional): Image file (JPG, PNG, etc.)
- `video` (File, optional): Video file (MP4, AVI, etc.)

**At least one file (image or video) must be provided.**

**Example (Image only):**
```bash
curl -X POST http://localhost:8095/api/media/upload \
  -F "truck_id=1753" \
  -F "image=@truck.jpg"
```

**Example (Video only):**
```bash
curl -X POST http://localhost:8095/api/media/upload \
  -F "truck_id=1753" \
  -F "video=@truck.mp4"
```

**Example (Both):**
```bash
curl -X POST http://localhost:8095/api/media/upload \
  -F "truck_id=1753" \
  -F "image=@truck.jpg" \
  -F "video=@truck.mp4"
```

---

### GET `/uploads/{file_type}/{filename}`

Access uploaded media files.

**Parameters:**
- `file_type`: `images`, `videos`, or `thumbnails`
- `filename`: The filename returned from upload

**Example:**
```bash
curl http://localhost:8095/uploads/images/truck_1753_20251016_125514_95d0f6bc.jpg
```

Or open directly in browser:
```
http://localhost:8095/uploads/images/truck_1753_20251016_125514_95d0f6bc.jpg
```

---

### DELETE `/api/media/truck/{truck_id}/media`

Delete all media files for a truck.

**Example:**
```bash
curl -X DELETE http://localhost:8095/api/media/truck/1753/media
```

---

## 🐍 Python Example

### Complete Workflow

```python
import requests
from pathlib import Path

API_URL = "http://localhost:8095"

# Step 1: Post truck detection
truck_data = {
    "id": 1,
    "timestamp": "2025-10-16T14:30:45",
    "length_mm": 12500,
    "height_mm": 3400,
    "is_truck": True,
    "classification_confidence": 0.94,
    "image_path": "truck_001.jpg",
    "video_path": "truck_001.mp4",
    "direction": 1,
    "speed_kmh": 68.5
}

response = requests.post(f"{API_URL}/api/truck-count", json=truck_data)
result = response.json()
truck_id = result['truck_id']

print(f"✅ Truck recorded: ID {truck_id}")

# Step 2: Upload media
files = {
    'image': open('truck_image.jpg', 'rb'),
    'video': open('truck_video.mp4', 'rb')
}
data = {'truck_id': truck_id}

response = requests.post(f"{API_URL}/api/media/upload", files=files, data=data)
result = response.json()

print(f"✅ Media uploaded!")
print(f"   Image: {result['truck']['image_url']}")
print(f"   Video: {result['truck']['video_url']}")

# Close files
for f in files.values():
    f.close()
```

### With Error Handling

```python
import requests
from datetime import datetime

def post_truck_with_media(truck_data, image_path, video_path=None):
    """Post truck detection and upload media"""
    try:
        # Step 1: Post truck data
        response = requests.post(
            "http://localhost:8095/api/truck-count",
            json=truck_data,
            timeout=10
        )
        response.raise_for_status()
        truck_id = response.json()['truck_id']
        
        # Step 2: Upload media
        files = {'image': open(image_path, 'rb')}
        if video_path:
            files['video'] = open(video_path, 'rb')
        
        data = {'truck_id': truck_id}
        
        response = requests.post(
            "http://localhost:8095/api/media/upload",
            files=files,
            data=data,
            timeout=30
        )
        response.raise_for_status()
        
        # Close files
        for f in files.values():
            f.close()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Usage
result = post_truck_with_media(
    truck_data={
        "id": 1,
        "timestamp": datetime.now().isoformat(),
        "length_mm": 12500,
        "height_mm": 3400,
        "is_truck": True,
        "classification_confidence": 0.94,
        "image_path": "truck.jpg",
        "video_path": "truck.mp4",
        "direction": 1,
        "speed_kmh": 68.5
    },
    image_path="/path/to/truck.jpg",
    video_path="/path/to/truck.mp4"
)

if result:
    print(f"Success! Truck ID: {result['truck_id']}")
```

---

## 🔧 Raspberry Pi Integration

### Camera Capture → Upload

```python
#!/usr/bin/env python3
import requests
import io
from datetime import datetime
from picamera2 import Picamera2
import time

API_URL = "http://your-server:8095"

# Initialize camera
camera = Picamera2()
camera.start()

def capture_and_upload(detection_id, truck_length_mm, confidence):
    """Capture image and upload to server"""
    
    # Step 1: Capture image
    image_stream = io.BytesIO()
    camera.capture_file(image_stream, format='jpeg')
    image_stream.seek(0)
    
    # Step 2: Post truck data
    truck_data = {
        "id": detection_id,
        "timestamp": datetime.now().isoformat(),
        "length_mm": truck_length_mm,
        "height_mm": 3000,  # estimated
        "is_truck": True,
        "classification_confidence": confidence,
        "image_path": f"truck_{detection_id}.jpg",
        "video_path": "",
        "direction": 1,
        "speed_kmh": 0.0
    }
    
    response = requests.post(f"{API_URL}/api/truck-count", json=truck_data)
    truck_id = response.json()['truck_id']
    
    # Step 3: Upload image
    files = {'image': ('truck.jpg', image_stream, 'image/jpeg')}
    data = {'truck_id': truck_id}
    
    response = requests.post(f"{API_URL}/api/media/upload", files=files, data=data)
    
    print(f"✅ Uploaded truck {truck_id}")
    return truck_id

# Main loop
detection_id = 1
while True:
    # Your truck detection logic here
    truck_detected = check_for_truck()
    
    if truck_detected:
        truck_id = capture_and_upload(
            detection_id=detection_id,
            truck_length_mm=12000,
            confidence=0.92
        )
        detection_id += 1
    
    time.sleep(1)
```

---

## 📁 File Storage

### Directory Structure

```
truck_monitoring/
├── backend/
│   ├── uploads/
│   │   ├── images/
│   │   │   └── truck_1753_20251016_125514_95d0f6bc.jpg
│   │   ├── videos/
│   │   │   └── truck_1753_20251016_125514_847945a0.mp4
│   │   └── thumbnails/
│   │       └── truck_1753_20251016_125514_95d0f6bc.jpg
```

### Filename Format

Files are automatically renamed to:
```
truck_{truck_id}_{timestamp}_{uuid}.{ext}
```

**Example:**
- `truck_1753_20251016_125514_95d0f6bc.jpg`
- `truck_1753_20251016_125514_847945a0.mp4`

**Benefits:**
- Unique filenames (no collisions)
- Sortable by timestamp
- Easy to identify truck
- Preserves original file extension

---

## ⚙️ Configuration

### File Size Limits

Default FastAPI limits:
- **Max file size:** 16 MB per request
- **Max request size:** 16 MB total

To change, update in `main.py`:
```python
from fastapi import FastAPI

app = FastAPI()

# Increase file size limit
app.add_middleware(
    ...,
    max_upload_size=50 * 1024 * 1024  # 50 MB
)
```

### Supported File Types

**Images:**
- JPG/JPEG
- PNG
- BMP
- TIFF
- WebP

**Videos:**
- MP4
- AVI
- MOV
- MKV
- WebM

No file type validation is enforced by default. All files are accepted.

---

## 🔒 Security Considerations

### Current Implementation

✅ **No authentication required** - Designed for trusted edge devices  
✅ **Unique filenames** - Prevents overwrites  
✅ **Isolated storage** - Files stored in dedicated directory  
⚠️ **No file type validation** - All files accepted  
⚠️ **No file size validation** - Limited by FastAPI defaults  
⚠️ **No virus scanning** - Not implemented  

### Production Recommendations

1. **File Type Validation**
```python
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png'}
ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/avi'}

if image.content_type not in ALLOWED_IMAGE_TYPES:
    raise HTTPException(400, "Invalid image type")
```

2. **File Size Validation**
```python
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB

# Check file size before saving
```

3. **Virus Scanning**
```python
import clamd

scanner = clamd.ClamdUnixSocket()
scan_result = scanner.scan_stream(file.file)
```

4. **Rate Limiting**
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/media/upload")
@limiter.limit("10/minute")
async def upload_media(...):
    ...
```

5. **API Key Authentication**
```python
from fastapi import Header

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(403, "Invalid API key")
```

---

## 🐛 Troubleshooting

### Error: "Truck ID not found"

```json
{
  "detail": "Truck ID 9999 not found"
}
```

**Solution:** Make sure the `truck_id` exists. It must be returned from POST `/api/truck-count` first.

### Error: "No file uploaded"

The API requires at least one file (image or video).

**Solution:** Include `-F "image=@file.jpg"` or `-F "video=@file.mp4"`

### Error: "File too large"

FastAPI default limit is 16 MB.

**Solution:** 
- Compress your images/videos
- Or increase the limit in configuration

### Images not showing in UI

**Check:**
1. Files uploaded successfully?
2. Server serving `/uploads` directory?
3. CORS configured correctly?
4. Check browser console for errors

---

## 📈 Performance Tips

### 1. Async Upload

Don't wait for upload to complete:

```python
import threading

def async_upload(truck_id, image_path):
    thread = threading.Thread(
        target=upload_media,
        args=(truck_id, image_path)
    )
    thread.daemon = True
    thread.start()
```

### 2. Compress Before Upload

```python
from PIL import Image

img = Image.open('truck.jpg')
img.save('truck_compressed.jpg', quality=85, optimize=True)
```

### 3. Batch Uploads

Upload multiple trucks' media together if network is slow.

### 4. Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def upload_with_retry(truck_id, files):
    return requests.post(url, files=files, data={'truck_id': truck_id})
```

---

## ✅ Testing

Run the test script:

```bash
cd backend
python3 test_edge_with_media.py
```

**Expected output:**
```
✅ SUCCESS: Truck recorded successfully: Container
✅ SUCCESS: Media uploaded successfully
✅ Image accessible at: http://localhost:8095/uploads/images/...
```

---

## 📞 Support

- **API Docs:** http://localhost:8095/docs
- **Test Endpoint:** `curl http://localhost:8095/health`
- **View Images:** http://localhost:8095/uploads/images/

---

**Happy Uploading! 📸🚛**

*Last Updated: October 16, 2025*






