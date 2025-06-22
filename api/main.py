from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import shutil
import uuid
from pathlib import Path
import asyncio
import subprocess
import sys
from typing import List, Dict
import json
from datetime import datetime

# Add parent directory to path to import video_processor and nlpv2
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_processor import VideoProcessor
from nlpv2.main import read_folder_raw, generate_narrative, save_narrative

app = FastAPI(title="Video Processing & Narrative Generation API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for job status
jobs = {}

class JobStatus:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "uploading"
        self.progress = 0
        self.message = "Starting upload..."
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.completed_at = None

@app.get("/")
async def root():
    return {"message": "Video Processing & Narrative Generation API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/upload-videos")
async def upload_videos(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Upload multiple videos and process them asynchronously."""
    
    # Validate files
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    
    for file in files:
        if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {file.filename}. Supported: {', '.join(valid_extensions)}"
            )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(job_id)
    
    # Start background processing
    background_tasks.add_task(process_videos_background, job_id, files)
    
    return {
        "job_id": job_id,
        "message": f"Uploaded {len(files)} videos. Processing started.",
        "status_endpoint": f"/job/{job_id}"
    }

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a processing job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }

@app.get("/jobs")
async def list_jobs():
    """List all jobs."""
    return {
        "jobs": [
            {
                "job_id": job.job_id,
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs.values()
        ]
    }

async def process_videos_background(job_id: str, files: List[UploadFile]):
    """Background task to process uploaded videos."""
    job = jobs[job_id]
    
    try:
        # Create temporary directories
        temp_dir = tempfile.mkdtemp(prefix="video_upload_")
        processed_dir = os.path.join(temp_dir, "processed")
        os.makedirs(processed_dir, exist_ok=True)
        
        job.status = "uploading"
        job.message = "Saving uploaded files..."
        job.progress = 10
        
        # Save uploaded files
        video_files = []
        for i, file in enumerate(files):
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            video_files.append(file_path)
            
            job.progress = 10 + (i + 1) * 20 // len(files)
        
        job.status = "processing"
        job.message = "Processing videos with AI..."
        job.progress = 30
        
        # Process videos using video_processor
        processor = VideoProcessor()
        
        for i, video_path in enumerate(video_files):
            job.message = f"Processing video {i+1}/{len(video_files)}: {os.path.basename(video_path)}"
            job.progress = 30 + (i + 1) * 40 // len(video_files)
            
            output_file = os.path.join(processed_dir, f"{Path(video_path).stem}_processed.txt")
            processor.process_video(video_path, output_file)
        
        job.status = "generating_narrative"
        job.message = "Generating narrative from processed content..."
        job.progress = 80
        
        # Generate narrative using nlpv2
        content = read_folder_raw(processed_dir)
        if content:
            narrative = generate_narrative(content)
            
            # Save narrative
            output_file = save_narrative(narrative, "api_outputs")
            
            job.status = "completed"
            job.message = "Processing completed successfully!"
            job.progress = 100
            job.result = {
                "narrative": narrative,
                "output_file": output_file,
                "processed_files": len([f for f in os.listdir(processed_dir) if f.endswith('.txt')])
            }
        else:
            raise Exception("No content found in processed files")
            
    except Exception as e:
        job.status = "error"
        job.message = f"Error during processing: {str(e)}"
        job.error = str(e)
        print(f"Error processing job {job_id}: {e}")
    
    finally:
        job.completed_at = datetime.now()
        
        # Clean up temporary files
        try:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its data."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del jobs[job_id]
    return {"message": "Job deleted successfully"}

@app.delete("/jobs")
async def clear_all_jobs():
    """Clear all jobs."""
    jobs.clear()
    return {"message": "All jobs cleared successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 