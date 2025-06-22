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

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

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
        if not file.filename or not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
            filename = file.filename or "unknown_file"
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {filename}. Supported: {', '.join(valid_extensions)}"
            )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(job_id)
    
    # Read file contents before starting background task
    # This prevents "read of closed file" errors
    file_data_list = []
    for file in files:
        file_content = await file.read()
        file_data_list.append({
            'filename': file.filename,
            'content': file_content,
            'content_type': file.content_type
        })
    
    # Start background processing with file data instead of file objects
    background_tasks.add_task(process_videos_background, job_id, file_data_list)
    
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

async def process_videos_background(job_id: str, file_data_list: List[dict]):
    """Background task to process uploaded videos."""
    job = jobs[job_id]
    
    print(f"🚀 Starting background processing for job {job_id}")
    print(f"📁 Processing {len(file_data_list)} files: {[f['filename'] for f in file_data_list]}")
    
    try:
        # Create temporary directories
        temp_dir = tempfile.mkdtemp(prefix="video_upload_")
        processed_dir = os.path.join(temp_dir, "processed")
        os.makedirs(processed_dir, exist_ok=True)
        
        print(f"📂 Created temp directories: {temp_dir}")
        
        job.status = "uploading"
        job.message = "Saving uploaded files..."
        job.progress = 10
        print(f"🔄 Job {job_id}: {job.message} (Progress: {job.progress}%)")
        
        # Save uploaded files from the pre-read data
        video_files = []
        for i, file_data in enumerate(file_data_list):
            file_path = os.path.join(temp_dir, file_data['filename'])
            
            # Write the pre-read content to file
            with open(file_path, "wb") as buffer:
                buffer.write(file_data['content'])
            
            video_files.append(file_path)
            job.progress = 10 + (i + 1) * 20 // len(file_data_list)
            print(f"📥 Saved file: {file_data['filename']} ({len(file_data['content'])} bytes)")
        
        job.status = "processing"
        job.message = "Processing videos with AI..."
        job.progress = 30
        print(f"🔄 Job {job_id}: {job.message} (Progress: {job.progress}%)")
        
        # Process videos using video_processor
        print(f"🎬 Initializing VideoProcessor...")
        processor = VideoProcessor()
        
        for i, video_path in enumerate(video_files):
            job.message = f"Processing video {i+1}/{len(video_files)}: {os.path.basename(video_path)}"
            job.progress = 30 + (i + 1) * 40 // len(video_files)
            print(f"🔄 Job {job_id}: {job.message} (Progress: {job.progress}%)")
            
            output_file = os.path.join(processed_dir, f"{Path(video_path).stem}_processed.txt")
            print(f"🎥 Processing video: {video_path} -> {output_file}")
            
            try:
                processor.process_video(video_path, output_file)
                print(f"✅ Successfully processed: {os.path.basename(video_path)}")
            except Exception as e:
                print(f"❌ Error processing video {video_path}: {e}")
                raise e
        
        # Check what files were created
        txt_files = [f for f in os.listdir(processed_dir) if f.endswith('.txt')]
        print(f"📋 Found {len(txt_files)} txt files:")
        for txt_file in txt_files:
            file_path = os.path.join(processed_dir, txt_file)
            file_size = os.path.getsize(file_path)
            print(f"  - {txt_file} ({file_size} bytes)")
        
        job.status = "generating_narrative"
        job.message = "Generating narrative from processed content..."
        job.progress = 80
        print(f"🔄 Job {job_id}: {job.message} (Progress: {job.progress}%)")
        
        # Generate narrative using nlpv2
        print(f"📖 Reading processed content from: {processed_dir}")
        try:
            content = read_folder_raw(processed_dir)
            print(f"📄 Read content length: {len(content) if content else 0} characters")
            
            if content:
                print(f"🤖 Generating narrative with AI...")
                narrative = generate_narrative(content)
                print(f"📝 Generated narrative length: {len(narrative)} characters")
                
                # Save narrative
                print(f"💾 Saving narrative to api_outputs...")
                output_file = save_narrative(narrative, "api_outputs")
                print(f"💾 Narrative saved to: {output_file}")
                
                job.status = "completed"
                job.message = "Processing completed successfully!"
                job.progress = 100
                job.result = {
                    "narrative": narrative,
                    "output_file": output_file,
                    "processed_files": len(txt_files)
                }
                print(f"🎉 Job {job_id} completed successfully!")
                print(f"🎉 Result: narrative={len(narrative)} chars, output_file={output_file}, processed_files={len(txt_files)}")
            else:
                error_msg = "No content found in processed files"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
        except Exception as e:
            print(f"❌ Error in narrative generation: {e}")
            raise e
            
    except Exception as e:
        error_msg = str(e)
        job.status = "error"
        job.message = f"Error during processing: {error_msg}"
        job.error = error_msg
        print(f"❌ Job {job_id} failed: {error_msg}")
        print(f"❌ Full error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        job.completed_at = datetime.now()
        print(f"🏁 Job {job_id} finished at {job.completed_at} with status: {job.status}")
        
        # Clean up temporary files
        try:
            if 'temp_dir' in locals():
                print(f"🧹 Cleaning up temp directory: {temp_dir}")
                shutil.rmtree(temp_dir)
                print(f"🧹 Temp directory cleaned up successfully")
        except Exception as e:
            print(f"⚠️ Error cleaning up temp files: {e}")

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
    print("Starting API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 