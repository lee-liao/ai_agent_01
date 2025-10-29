#!/usr/bin/env python3
"""
Test script for edge computer API
This simulates an edge computer sending truck detection data to the server
"""

import requests
import json
from datetime import datetime

# Server endpoint (change port if needed)
API_URL = "http://localhost:8095/api/truck-count"

def send_truck_detection(truck_data):
    """Send truck detection data to the server"""
    try:
        response = requests.post(API_URL, json=truck_data)
        response.raise_for_status()
        result = response.json()
        print(f"✅ {result['status'].upper()}: {result['message']}")
        if result['truck_id'] > 0:
            print(f"   Truck ID: {result['truck_id']}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🚛 Edge Computer API Test")
    print("=" * 50)
    
    # Test 1: Valid truck detection
    print("\n📸 Test 1: Valid truck (Container)")
    truck1 = {
        "id": 101,
        "timestamp": datetime.now().isoformat(),
        "length_mm": 13500,
        "height_mm": 3500,
        "is_truck": True,
        "classification_confidence": 0.92,
        "image_path": "edge_truck_101.jpg",
        "video_path": "edge_truck_101.mp4",
        "direction": 1,  # Northbound
        "speed_kmh": 70.5
    }
    send_truck_detection(truck1)
    
    # Test 2: Valid truck detection (smaller truck)
    print("\n📸 Test 2: Valid truck (Box Truck)")
    truck2 = {
        "id": 102,
        "timestamp": datetime.now().isoformat(),
        "length_mm": 6500,
        "height_mm": 2800,
        "is_truck": True,
        "classification_confidence": 0.85,
        "image_path": "edge_truck_102.jpg",
        "video_path": "",
        "direction": 2,  # Southbound
        "speed_kmh": 55.0
    }
    send_truck_detection(truck2)
    
    # Test 3: Not a truck (should be skipped)
    print("\n📸 Test 3: Not a truck (car)")
    not_truck = {
        "id": 103,
        "timestamp": datetime.now().isoformat(),
        "length_mm": 4500,
        "height_mm": 1500,
        "is_truck": False,
        "classification_confidence": 0.80,
        "image_path": "car.jpg",
        "video_path": "",
        "direction": 1,
        "speed_kmh": 90.0
    }
    send_truck_detection(not_truck)
    
    # Test 4: Low confidence (should be skipped)
    print("\n📸 Test 4: Low confidence detection")
    low_confidence = {
        "id": 104,
        "timestamp": datetime.now().isoformat(),
        "length_mm": 8000,
        "height_mm": 2700,
        "is_truck": True,
        "classification_confidence": 0.42,  # Below 0.5 threshold
        "image_path": "uncertain.jpg",
        "video_path": "",
        "direction": 0,
        "speed_kmh": 60.0
    }
    send_truck_detection(low_confidence)
    
    # Test 5: Valid truck with different direction
    print("\n📸 Test 5: Valid truck (Eastbound)")
    truck5 = {
        "id": 105,
        "timestamp": datetime.now().isoformat(),
        "length_mm": 10500,
        "height_mm": 3100,
        "is_truck": True,
        "classification_confidence": 0.88,
        "image_path": "edge_truck_105.jpg",
        "video_path": "edge_truck_105.mp4",
        "direction": 3,  # Eastbound
        "speed_kmh": 65.0
    }
    send_truck_detection(truck5)
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\n💡 Check the dashboard at: http://localhost:8095/docs")
    print("   Or view frontend at: http://localhost:3000")

if __name__ == "__main__":
    main()






