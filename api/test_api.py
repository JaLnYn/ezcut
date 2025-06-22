#!/usr/bin/env python3
"""
Test script for the Video Processing & Narrative Generation API
"""

import requests
import time
import json
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    response = requests.get(f"{API_BASE_URL}/health")
    print("Health Check:", response.json())
    return response.status_code == 200

def upload_videos(video_files):
    """Upload videos to the API."""
    files = []
    for video_file in video_files:
        if Path(video_file).exists():
            files.append(('files', open(video_file, 'rb')))
        else:
            print(f"Warning: {video_file} not found")
    
    if not files:
        print("No valid video files found")
        return None
    
    response = requests.post(f"{API_BASE_URL}/upload-videos", files=files)
    
    # Close file handles
    for _, file in files:
        file.close()
    
    if response.status_code == 200:
        result = response.json()
        print("Upload successful:", result)
        return result['job_id']
    else:
        print("Upload failed:", response.text)
        return None

def monitor_job(job_id):
    """Monitor a job until completion."""
    print(f"Monitoring job: {job_id}")
    
    while True:
        response = requests.get(f"{API_BASE_URL}/job/{job_id}")
        
        if response.status_code == 200:
            job_status = response.json()
            print(f"Status: {job_status['status']} - {job_status['message']} ({job_status['progress']}%)")
            
            if job_status['status'] in ['completed', 'error']:
                if job_status['status'] == 'completed':
                    print("\n=== RESULT ===")
                    print("Narrative:", job_status['result']['narrative'])
                    print("Output file:", job_status['result']['output_file'])
                    print("Processed files:", job_status['result']['processed_files'])
                else:
                    print("\n=== ERROR ===")
                    print("Error:", job_status['error'])
                break
        else:
            print(f"Error checking job status: {response.text}")
            break
        
        time.sleep(5)  # Wait 5 seconds before checking again

def list_jobs():
    """List all jobs."""
    response = requests.get(f"{API_BASE_URL}/jobs")
    if response.status_code == 200:
        jobs = response.json()
        print("All jobs:", json.dumps(jobs, indent=2))
    else:
        print("Error listing jobs:", response.text)

def main():
    """Main test function."""
    print("=== Video Processing & Narrative Generation API Test ===\n")
    
    # Test health
    if not test_health():
        print("API is not running. Please start the server first.")
        return
    
    # Example video files (update these paths)
    video_files = [
        # "path/to/your/video1.mp4",
        # "path/to/your/video2.mp4",
    ]
    
    # If no video files specified, just show the API structure
    if not video_files or not any(Path(f).exists() for f in video_files):
        print("No video files specified. Here's how to use the API:")
        print("\n1. Start the server:")
        print("   cd api && python main.py")
        print("\n2. Upload videos:")
        print("   curl -X POST http://localhost:8000/upload-videos \\")
        print("     -F 'files=@video1.mp4' \\")
        print("     -F 'files=@video2.mp4'")
        print("\n3. Check job status:")
        print("   curl http://localhost:8000/job/{job_id}")
        print("\n4. List all jobs:")
        print("   curl http://localhost:8000/jobs")
        return
    
    # Upload videos
    job_id = upload_videos(video_files)
    if job_id:
        # Monitor the job
        monitor_job(job_id)
        
        # List all jobs
        print("\n=== All Jobs ===")
        list_jobs()

if __name__ == "__main__":
    main() 