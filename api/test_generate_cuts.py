#!/usr/bin/env python3
"""
Test script for the generate-cuts API endpoint
"""

import requests
import json
import time
import sys

# API base URL
API_BASE_URL = "http://localhost:8000"

def test_generate_cuts():
    """Test the generate-cuts endpoint"""
    
    # Test narrative text
    narrative_text = """
    This is a test narrative for video cuts generation. 
    The story follows a group of developers working on an exciting project.
    They face challenges, solve problems, and celebrate their successes together.
    The journey is filled with moments of collaboration, innovation, and teamwork.
    """
    
    # Test request
    request_data = {
        "narrative_text": narrative_text.strip(),
        "duration": 60,  # 1 minute
        "interval_duration": 5,  # 5 second intervals
        "job_id": None  # Use default directories
    }
    
    print("🧪 Testing generate-cuts API endpoint...")
    print(f"📝 Narrative length: {len(request_data['narrative_text'])} characters")
    print(f"⏱️ Duration: {request_data['duration']}s, Interval: {request_data['interval_duration']}s")
    print(f"🌐 API URL: {API_BASE_URL}/generate-cuts")
    
    try:
        # Call the API
        print("📡 Making API request...")
        response = requests.post(
            f"{API_BASE_URL}/generate-cuts",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📡 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            job_id = result["job_id"]
            print(f"✅ API call successful! Job ID: {job_id}")
            
            # Poll for completion
            print("🔄 Polling for job completion...")
            max_attempts = 60  # 60 attempts * 2 seconds = 2 minutes max
            attempts = 0
            
            while attempts < max_attempts:
                time.sleep(2)
                attempts += 1
                
                try:
                    status_response = requests.get(f"{API_BASE_URL}/job/{job_id}", timeout=10)
                    print(f"📊 Status check {attempts}: {status_response.status_code}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data["status"]
                        progress = status_data["progress"]
                        message = status_data["message"]
                        
                        print(f"📊 Attempt {attempts}: Status={status}, Progress={progress}%, Message={message}")
                        
                        if status == "completed":
                            print("🎉 Job completed successfully!")
                            result = status_data.get("result", {})
                            print(f"📹 Final video: {result.get('final_video_path', 'N/A')}")
                            print(f"📊 Intervals: {result.get('intervals_count', 0)}")
                            print(f"⏱️ Duration: {result.get('total_duration', 0)}s")
                            print(f"💾 File size: {result.get('final_video_size', 0)} bytes")
                            return True
                        elif status == "error":
                            error = status_data.get("error", "Unknown error")
                            print(f"❌ Job failed: {error}")
                            return False
                    else:
                        print(f"❌ Failed to get job status: {status_response.status_code}")
                        print(f"❌ Response: {status_response.text}")
                        return False
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ Request error on attempt {attempts}: {e}")
                    if attempts >= max_attempts:
                        return False
            
            print("⏰ Timeout waiting for job completion")
            return False
            
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"❌ Response headers: {dict(response.headers)}")
            print(f"❌ Response body: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request exception: {e}")
        return False
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check exception: {e}")
        return False

def main():
    print("🚀 Starting API tests...")
    print("=" * 50)
    
    # Test health check first
    if not test_health_check():
        print("❌ Health check failed, API server may not be running")
        print("💡 Make sure to start the API server with: python api/main.py")
        sys.exit(1)
    
    print()
    
    # Test generate-cuts
    if test_generate_cuts():
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 