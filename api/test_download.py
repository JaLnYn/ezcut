#!/usr/bin/env python3
"""
Test script for the download and preview endpoints
"""

import requests
import json
import time
import sys

# API base URL
API_BASE_URL = "http://localhost:8000"

def test_download_endpoints():
    """Test the download and preview endpoints"""
    
    print("🧪 Testing download and preview endpoints...")
    
    # First, get a list of jobs to find a completed one
    try:
        response = requests.get(f"{API_BASE_URL}/jobs")
        if response.status_code == 200:
            jobs_data = response.json()
            jobs = jobs_data.get('jobs', [])
            
            # Find a completed job
            completed_job = None
            for job in jobs:
                if job['status'] == 'completed':
                    completed_job = job
                    break
            
            if not completed_job:
                print("❌ No completed jobs found. Please run a video processing job first.")
                return False
            
            job_id = completed_job['job_id']
            print(f"📋 Found completed job: {job_id}")
            
            # Test preview endpoint
            print("🔍 Testing preview endpoint...")
            preview_response = requests.get(f"{API_BASE_URL}/preview/{job_id}")
            print(f"📊 Preview response status: {preview_response.status_code}")
            print(f"📊 Preview response headers: {dict(preview_response.headers)}")
            
            if preview_response.status_code == 200:
                print("✅ Preview endpoint working")
                content_length = preview_response.headers.get('content-length', 'unknown')
                print(f"📊 Video size: {content_length} bytes")
            else:
                print(f"❌ Preview failed: {preview_response.text}")
            
            # Test download endpoint
            print("🔍 Testing download endpoint...")
            download_response = requests.get(f"{API_BASE_URL}/download/{job_id}")
            print(f"📊 Download response status: {download_response.status_code}")
            print(f"📊 Download response headers: {dict(download_response.headers)}")
            
            if download_response.status_code == 200:
                print("✅ Download endpoint working")
                content_length = download_response.headers.get('content-length', 'unknown')
                content_disposition = download_response.headers.get('content-disposition', 'unknown')
                print(f"📊 Video size: {content_length} bytes")
                print(f"📊 Content disposition: {content_disposition}")
                
                # Save a small sample to verify it's a valid video file
                sample_filename = f"sample_video_{job_id[:8]}.mp4"
                with open(sample_filename, 'wb') as f:
                    f.write(download_response.content[:1024])  # Save first 1KB
                print(f"💾 Saved sample to: {sample_filename}")
                
            else:
                print(f"❌ Download failed: {download_response.text}")
            
            return True
            
        else:
            print(f"❌ Failed to get jobs: {response.status_code}")
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
    print("🚀 Starting download endpoint tests...")
    print("=" * 50)
    
    # Test health check first
    if not test_health_check():
        print("❌ Health check failed, API server may not be running")
        print("💡 Make sure to start the API server with: python api/main.py")
        sys.exit(1)
    
    print()
    
    # Test download endpoints
    if test_download_endpoints():
        print("\n🎉 Download endpoint tests completed!")
        sys.exit(0)
    else:
        print("\n❌ Download endpoint tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 