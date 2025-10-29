# 🚛 Edge Computer API Integration Guide

## Overview

The Truck Monitoring System now includes a dedicated API endpoint for edge computers to send truck detection data in real-time. This endpoint is designed for IoT devices, cameras, and edge computing systems that perform truck detection and classification.

## 📡 Endpoint

```
POST http://localhost:8095/api/truck-count
```

**Note:** This endpoint does NOT require authentication, making it suitable for edge devices.

---

## 📋 Request Format

### Headers
```
Content-Type: application/json
```

### Request Body

```json
{
  "id": 1,                              // Unique detection ID from edge device
  "timestamp": "2025-10-16T14:30:45",  // ISO 8601 format
  "length_mm": 8500,                    // Truck length in millimeters
  "height_mm": 2800,                    // Truck height in millimeters
  "is_truck": true,                     // Boolean: true if classified as truck
  "classification_confidence": 0.87,    // Confidence score (0.0 - 1.0)
  "image_path": "test.jpg",            // Path/name of captured image
  "video_path": "",                     // Optional: path to video
  "direction": 0,                       // Direction code (see below)
  "speed_kmh": 0.0                      // Speed in km/h (optional)
}
```

### Direction Codes

| Code | Direction   | Description        |
|------|-------------|--------------------|
| 0    | Unknown     | Direction not detected |
| 1    | Northbound  | Traveling north    |
| 2    | Southbound  | Traveling south    |
| 3    | Eastbound   | Traveling east     |
| 4    | Westbound   | Traveling west     |

---

## 📤 Response Format

### Success Response

```json
{
  "status": "success",
  "message": "Truck recorded successfully: Flatbed",
  "truck_id": 1744,
  "timestamp": "2025-10-16T14:30:45"
}
```

### Skipped Response (Not a Truck)

```json
{
  "status": "skipped",
  "message": "Not classified as a truck",
  "truck_id": 0,
  "timestamp": "2025-10-16T16:00:00"
}
```

### Skipped Response (Low Confidence)

```json
{
  "status": "skipped",
  "message": "Confidence too low: 0.45",
  "truck_id": 0,
  "timestamp": "2025-10-16T16:15:00"
}
```

---

## 🔧 Features

### 1. Automatic Truck Classification

Trucks are automatically classified based on their length:

| Length (meters) | Classification |
|-----------------|----------------|
| >= 12.0 m       | Container      |
| >= 8.0 m        | Flatbed        |
| >= 6.0 m        | Box Truck      |
| < 6.0 m         | Small Truck    |

### 2. Confidence Threshold

- **Minimum confidence:** 0.5 (50%)
- Detections below this threshold are rejected
- Configurable in the source code (`edge.py`)

### 3. Automatic Statistics Updates

When a truck is recorded:
- Daily statistics are automatically updated
- Hourly traffic patterns are recalculated
- Type counts are updated
- Peak hour detection is refreshed

### 4. Data Validation

The API automatically:
- ✅ Validates timestamp format
- ✅ Converts length from mm to meters
- ✅ Maps direction codes to readable names
- ✅ Rejects non-truck detections
- ✅ Filters low-confidence detections

---

## 🧪 Testing

### Using cURL

```bash
# Test 1: Valid truck detection
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

# Test 2: With video and direction
curl -X POST http://localhost:8095/api/truck-count \
  -H "Content-Type: application/json" \
  -d '{
    "id": 2,
    "timestamp": "2025-10-16T15:45:30",
    "length_mm": 12500,
    "height_mm": 3200,
    "is_truck": true,
    "classification_confidence": 0.95,
    "image_path": "truck_002.jpg",
    "video_path": "truck_002.mp4",
    "direction": 1,
    "speed_kmh": 65.5
  }'
```

### Using Python

A test script is provided at `backend/test_edge_api.py`:

```bash
cd backend
python3 test_edge_api.py
```

### Using Python Requests

```python
import requests
from datetime import datetime

url = "http://localhost:8095/api/truck-count"

data = {
    "id": 101,
    "timestamp": datetime.now().isoformat(),
    "length_mm": 10500,
    "height_mm": 3100,
    "is_truck": True,
    "classification_confidence": 0.88,
    "image_path": "truck_101.jpg",
    "video_path": "truck_101.mp4",
    "direction": 3,  # Eastbound
    "speed_kmh": 65.0
}

response = requests.post(url, json=data)
print(response.json())
```

---

## 🔄 Integration Examples

### Raspberry Pi with Camera

```python
#!/usr/bin/env python3
import requests
import time
from datetime import datetime
from your_detection_module import detect_truck

API_URL = "http://your-server:8095/api/truck-count"

def send_detection(detection):
    """Send detection to server"""
    data = {
        "id": detection['id'],
        "timestamp": datetime.now().isoformat(),
        "length_mm": detection['length'],
        "height_mm": detection['height'],
        "is_truck": detection['is_truck'],
        "classification_confidence": detection['confidence'],
        "image_path": detection['image_path'],
        "video_path": detection['video_path'],
        "direction": detection['direction'],
        "speed_kmh": detection['speed']
    }
    
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending detection: {e}")
        return None

# Main detection loop
while True:
    detection = detect_truck()  # Your detection logic
    if detection:
        result = send_detection(detection)
        if result:
            print(f"✅ Sent: {result['status']}")
    time.sleep(1)
```

### Arduino/ESP32

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* serverUrl = "http://your-server:8095/api/truck-count";

void sendTruckDetection(int id, float length_mm, float height_mm, 
                        float confidence, int direction, float speed) {
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<512> doc;
  doc["id"] = id;
  doc["timestamp"] = getCurrentTimestamp();  // Implement this
  doc["length_mm"] = length_mm;
  doc["height_mm"] = height_mm;
  doc["is_truck"] = true;
  doc["classification_confidence"] = confidence;
  doc["image_path"] = "esp32_" + String(id) + ".jpg";
  doc["video_path"] = "";
  doc["direction"] = direction;
  doc["speed_kmh"] = speed;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpCode = http.POST(jsonString);
  
  if (httpCode > 0) {
    String response = http.getString();
    Serial.println("Response: " + response);
  }
  
  http.end();
}
```

---

## 📊 Data Storage

### Database Record

Each accepted truck detection creates a record in the `trucks` table:

```sql
truck_number:     "EDGE-{id}-{timestamp}"
license_plate:    NULL
truck_type:       Auto-classified based on length
length_meters:    Converted from length_mm
speed_kmh:        From detection or NULL
location:         "Edge Detection Point"
direction:        Mapped from direction code
pass_time:        From timestamp
date:             YYYY-MM-DD format
image_url:        "/uploads/images/{image_path}"
video_url:        "/uploads/videos/{video_path}"
notes:            "Edge detection | Confidence: XX% | Height: XXXXmm"
```

### Media Files

Images and videos should be uploaded separately to:
- Images: `/uploads/images/`
- Videos: `/uploads/videos/`
- Thumbnails: `/uploads/thumbnails/`

The API only stores the paths/filenames, not the actual files.

---

## 🛡️ Security Considerations

### Current Implementation

- ⚠️ **No authentication required** - Designed for trusted internal networks
- ✅ Confidence threshold prevents garbage data
- ✅ Validation prevents malformed requests
- ✅ Database transactions ensure data integrity

### Recommended for Production

1. **API Key Authentication**
   - Add API key header validation
   - Rotate keys periodically

2. **IP Whitelisting**
   - Only accept requests from known edge devices
   - Use firewall rules

3. **Rate Limiting**
   - Prevent spam/abuse
   - Max requests per device per minute

4. **HTTPS**
   - Encrypt data in transit
   - Use SSL/TLS certificates

5. **Data Sanitization**
   - Validate image paths
   - Prevent directory traversal attacks

---

## 🐛 Troubleshooting

### Connection Refused

```
Error: Connection refused
```

**Solutions:**
- Check if server is running: `curl http://localhost:8095/health`
- Verify server address and port
- Check firewall rules

### Invalid Timestamp

```
Error: Invalid timestamp format
```

**Solution:** Use ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`

```python
from datetime import datetime
timestamp = datetime.now().isoformat()
```

### Detection Skipped

```
status: "skipped"
```

**Reasons:**
1. `is_truck == false` - Not classified as truck
2. `classification_confidence < 0.5` - Confidence too low

**Solutions:**
- Improve detection algorithm
- Adjust confidence threshold in `edge.py`

### Server Error 500

```
Error: 500 Internal Server Error
```

**Solutions:**
- Check server logs: `tail -f backend/server.log`
- Verify database is accessible
- Check data format matches schema

---

## 📈 Performance

### Capacity

- **Throughput:** ~100 requests/second (tested)
- **Database:** SQLite (dev) or MySQL (production)
- **Storage:** Minimal - only metadata stored

### Optimization Tips

1. **Batch Processing**
   - Send detections in batches if multiple trucks detected
   - Reduces network overhead

2. **Async Requests**
   - Don't block detection pipeline waiting for API response
   - Use background threads/tasks

3. **Local Buffering**
   - Buffer detections locally during network outages
   - Retry failed submissions

---

## 📞 Support

### API Documentation

Interactive API docs: http://localhost:8095/docs

### Test Endpoints

```bash
# Health check
curl http://localhost:8095/health

# API root
curl http://localhost:8095/

# OpenAPI spec
curl http://localhost:8095/openapi.json
```

### Log Files

Server logs: `backend/server.log`

---

## 🎯 Next Steps

1. ✅ **Test the endpoint** - Run `test_edge_api.py`
2. ✅ **View results** - Check dashboard at http://localhost:8095/docs
3. 🔧 **Integrate with your edge device** - Use examples above
4. 📊 **Monitor statistics** - View daily/hourly trends
5. 🚀 **Deploy to production** - Add security measures

---

**Happy Monitoring! 🚛📊**

*Last Updated: October 16, 2025*






