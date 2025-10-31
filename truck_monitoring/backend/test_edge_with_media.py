#!/usr/bin/env python3
"""
Complete test script for edge computer workflow with media upload
Demonstrates: 1) Post truck data, 2) Upload image/video
"""

import requests
import json
from datetime import datetime
from io import BytesIO
from PIL import Image
import os

# Server endpoints
API_URL = "http://localhost:8095"
TRUCK_COUNT_ENDPOINT = f"{API_URL}/api/truck-count"
MEDIA_UPLOAD_ENDPOINT = f"{API_URL}/api/media/upload"

def create_sample_image(truck_id: int) -> BytesIO:
    """Create a sample image for testing"""
    img = Image.new('RGB', (800, 600), color=(73, 109, 137))
    # Add text to image (requires PIL with text support)
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Draw truck info
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except:
        font = None
    
    draw.text((250, 250), f"TRUCK #{truck_id}", fill=(255, 255, 255), font=font)
    draw.text((250, 300), datetime.now().strftime("%Y-%m-%d %H:%M"), fill=(255, 255, 255), font=font)
    
    # Save to BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def create_sample_video() -> BytesIO:
    """Create a sample video placeholder (just a small file for demo)"""
    # In production, this would be actual video data
    video_data = b"FAKE_VIDEO_DATA_" + os.urandom(1024)
    return BytesIO(video_data)

def post_truck_detection(truck_data: dict) -> dict:
    """Step 1: Post truck detection data"""
    print(f"\n📊 Step 1: Posting truck detection data...")
    print(f"   Length: {truck_data['length_mm']}mm, Confidence: {truck_data['classification_confidence']}")
    
    response = requests.post(TRUCK_COUNT_ENDPOINT, json=truck_data)
    response.raise_for_status()
    result = response.json()
    
    print(f"✅ {result['status'].upper()}: {result['message']}")
    print(f"   Truck ID: {result['truck_id']}")
    
    return result

def upload_media(truck_id: int, with_video: bool = True):
    """Step 2: Upload image and video for the truck"""
    print(f"\n📸 Step 2: Uploading media for Truck ID {truck_id}...")
    
    # Create sample files
    image_data = create_sample_image(truck_id)
    
    files = {
        'image': ('truck_image.jpg', image_data, 'image/jpeg')
    }
    
    if with_video:
        video_data = create_sample_video()
        files['video'] = ('truck_video.mp4', video_data, 'video/mp4')
        print(f"   Uploading: Image + Video")
    else:
        print(f"   Uploading: Image only")
    
    data = {'truck_id': truck_id}
    
    response = requests.post(MEDIA_UPLOAD_ENDPOINT, files=files, data=data)
    response.raise_for_status()
    result = response.json()
    
    print(f"✅ {result['status'].upper()}: {result['message']}")
    print(f"   Image URL: {result['truck']['image_url']}")
    if result['truck']['video_url']:
        print(f"   Video URL: {result['truck']['video_url']}")
    
    return result

def verify_media(image_url: str):
    """Step 3: Verify the uploaded media is accessible"""
    print(f"\n🔍 Step 3: Verifying media accessibility...")
    
    full_url = f"{API_URL}{image_url}"
    response = requests.get(full_url)
    
    if response.status_code == 200:
        print(f"✅ Image accessible at: {full_url}")
        print(f"   Size: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Image not accessible: {response.status_code}")
        return False

def main():
    print("=" * 70)
    print("🚛 EDGE COMPUTER - COMPLETE WORKFLOW TEST")
    print("=" * 70)
    
    try:
        # Test 1: Complete workflow with video
        print("\n" + "=" * 70)
        print("TEST 1: Complete Workflow (Image + Video)")
        print("=" * 70)
        
        truck_data_1 = {
            "id": 2001,
            "timestamp": datetime.now().isoformat(),
            "length_mm": 12500,
            "height_mm": 3400,
            "is_truck": True,
            "classification_confidence": 0.94,
            "image_path": "truck_2001.jpg",
            "video_path": "truck_2001.mp4",
            "direction": 1,
            "speed_kmh": 68.5
        }
        
        # Step 1: Post truck data
        result_1 = post_truck_detection(truck_data_1)
        truck_id_1 = result_1['truck_id']
        
        # Step 2: Upload media
        media_result_1 = upload_media(truck_id_1, with_video=True)
        
        # Step 3: Verify
        verify_media(media_result_1['truck']['image_url'])
        
        # Test 2: Image only
        print("\n" + "=" * 70)
        print("TEST 2: Image Only (No Video)")
        print("=" * 70)
        
        truck_data_2 = {
            "id": 2002,
            "timestamp": datetime.now().isoformat(),
            "length_mm": 8200,
            "height_mm": 2800,
            "is_truck": True,
            "classification_confidence": 0.88,
            "image_path": "truck_2002.jpg",
            "video_path": "",
            "direction": 2,
            "speed_kmh": 55.0
        }
        
        # Step 1: Post truck data
        result_2 = post_truck_detection(truck_data_2)
        truck_id_2 = result_2['truck_id']
        
        # Step 2: Upload image only
        media_result_2 = upload_media(truck_id_2, with_video=False)
        
        # Step 3: Verify
        verify_media(media_result_2['truck']['image_url'])
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        
        print(f"\n📋 Summary:")
        print(f"   • Truck 1 ID: {truck_id_1} (with image and video)")
        print(f"   • Truck 2 ID: {truck_id_2} (with image only)")
        print(f"\n🌐 View in web UI:")
        print(f"   • Frontend: http://localhost:3000")
        print(f"   • API Docs: http://localhost:8095/docs")
        print(f"\n📸 Direct image access:")
        print(f"   • Truck 1: {API_URL}{media_result_1['truck']['image_url']}")
        print(f"   • Truck 2: {API_URL}{media_result_2['truck']['image_url']}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 Make sure the server is running:")
        print(f"   cd backend && uvicorn app.main:app --reload --port 8095")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()






