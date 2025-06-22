from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
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
from typing import List, Dict, Optional
import json
from datetime import datetime
from pydantic import BaseModel

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path to import video_processor and nlpv2
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_processor import VideoProcessor
from nlpv2.main import read_folder_raw, generate_narrative, save_narrative

# Add the parent directory to sys.path to access the scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create job_data directory if it doesn't exist
os.makedirs("job_data", exist_ok=True)

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

class GenerateCutsRequest(BaseModel):
    narrative_text: str
    duration: int = 120
    interval_duration: int = 10
    job_id: Optional[str] = None  # If provided, use existing job's processed files

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
        # Create persistent directories for this job
        job_dir = os.path.join("job_data", job_id)
        videos_dir = os.path.join(job_dir, "videos")
        processed_dir = os.path.join(job_dir, "processed")
        
        os.makedirs(videos_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        
        print(f"📂 Created job directories: {job_dir}")
        
        job.status = "uploading"
        job.message = "Saving uploaded files..."
        job.progress = 10
        print(f"🔄 Job {job_id}: {job.message} (Progress: {job.progress}%)")
        
        # Save uploaded files to persistent location
        video_files = []
        for i, file_data in enumerate(file_data_list):
            file_path = os.path.join(videos_dir, file_data['filename'])
            
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
                    "processed_files": len(txt_files),
                    "job_directory": job_dir,
                    "videos_directory": videos_dir,
                    "processed_directory": processed_dir
                }
                print(f"🎉 Job {job_id} completed successfully!")
                print(f"🎉 Result: narrative={len(narrative)} chars, output_file={output_file}, processed_files={len(txt_files)}")
                print(f"🎉 Job data saved to: {job_dir}")
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
        # Note: We no longer clean up the job directory to preserve files for generate-cuts

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its data."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up job data directory
    job_dir = os.path.join("job_data", job_id)
    if os.path.exists(job_dir):
        try:
            shutil.rmtree(job_dir)
            print(f"🧹 Cleaned up job directory: {job_dir}")
        except Exception as e:
            print(f"⚠️ Error cleaning up job directory {job_dir}: {e}")
    
    del jobs[job_id]
    return {"message": "Job deleted successfully"}

@app.delete("/jobs")
async def clear_all_jobs():
    """Clear all jobs."""
    # Clean up all job data directories
    job_data_dir = "job_data"
    if os.path.exists(job_data_dir):
        try:
            shutil.rmtree(job_data_dir)
            print(f"🧹 Cleaned up all job directories: {job_data_dir}")
        except Exception as e:
            print(f"⚠️ Error cleaning up job directories {job_data_dir}: {e}")
    
    jobs.clear()
    return {"message": "All jobs cleared successfully"}

@app.post("/generate-cuts")
async def generate_cuts(
    background_tasks: BackgroundTasks,
    request: GenerateCutsRequest
):
    """Generate video cuts from narrative text using the interval generation and cutting scripts."""
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(job_id)
    
    # Start background processing
    background_tasks.add_task(generate_cuts_background, job_id, request)
    
    return {
        "job_id": job_id,
        "message": "Video cuts generation started.",
        "status_endpoint": f"/job/{job_id}"
    }

async def generate_cuts_background(job_id: str, request: GenerateCutsRequest):
    """Background task to generate video cuts from narrative text."""
    job = jobs[job_id]
    
    print(f"🎬 Starting video cuts generation for job {job_id}")
    print(f"📝 Narrative length: {len(request.narrative_text)} characters")
    print(f"⏱️ Target duration: {request.duration}s, Interval duration: {request.interval_duration}s")
    
    try:
        # Create temporary directories
        temp_dir = tempfile.mkdtemp(prefix="video_cuts_")
        narrative_file = os.path.join(temp_dir, "narrative.txt")
        intervals_file = os.path.join(temp_dir, "intervals.json")
        output_dir = os.path.join(temp_dir, "output_segments")
        final_video = os.path.join(temp_dir, "final_cut_video.mp4")
        
        print(f"📂 Created temp directory: {temp_dir}")
        
        # Step 1: Save narrative text to file
        job.status = "preparing"
        job.message = "Preparing narrative file..."
        job.progress = 10
        print(f"🔄 Job {job_id}: {job.message} (Progress: {job.progress}%)")
        
        with open(narrative_file, 'w', encoding='utf-8') as f:
            f.write(request.narrative_text)
        print(f"📝 Saved narrative to: {narrative_file}")
        
        # Step 2: Determine source directories
        if request.job_id and request.job_id in jobs:
            # Use existing job's processed files
            existing_job = jobs[request.job_id]
            if existing_job.status == "completed" and existing_job.result:
                # Use the actual directories from the existing job
                stream_dir = existing_job.result.get("processed_directory", "stream_processed_clip")
                video_dir = existing_job.result.get("videos_directory", "stream_videos")
                print(f"📁 Using existing job {request.job_id} files:")
                print(f"  - Videos: {video_dir}")
                print(f"  - Processed: {stream_dir}")
            else:
                raise Exception(f"Job {request.job_id} is not completed or has no result")
        else:
            # Use default directories
            stream_dir = "stream_processed_clip"
            video_dir = "stream_videos"
            print(f"📁 Using default directories: {stream_dir}, {video_dir}")
        
        # Check if directories exist
        print(f"🔍 Checking directory existence:")
        print(f"  - Stream dir ({stream_dir}): {os.path.exists(stream_dir)}")
        print(f"  - Video dir ({video_dir}): {os.path.exists(video_dir)}")
        
        if not os.path.exists(stream_dir):
            print(f"⚠️ Warning: Stream directory {stream_dir} does not exist")
        if not os.path.exists(video_dir):
            print(f"⚠️ Warning: Video directory {video_dir} does not exist")
        
        # List contents of directories if they exist
        if os.path.exists(stream_dir):
            stream_files = os.listdir(stream_dir)
            print(f"📋 Stream directory contents ({len(stream_files)} files): {stream_files[:5]}{'...' if len(stream_files) > 5 else ''}")
        
        if os.path.exists(video_dir):
            video_files = os.listdir(video_dir)
            print(f"📋 Video directory contents ({len(video_files)} files): {video_files[:5]}{'...' if len(video_files) > 5 else ''}")
        
        # Step 3: Generate intervals
        job.status = "generating_intervals"
        job.message = "Generating video intervals from narrative..."
        job.progress = 30
        print(f"🔄 Job {job_id}: {job.message} (Progress: {job.progress}%)")
        
        intervals_success = await run_generate_intervals(
            narrative_file, stream_dir, intervals_file, 
            request.duration, request.interval_duration
        )
        
        if not intervals_success:
            raise Exception("Failed to generate intervals")
        
        # Check if intervals file was created
        print(f"🔍 Checking if intervals file exists: {intervals_file}")
        print(f"🔍 Intervals file exists: {os.path.exists(intervals_file)}")
        if os.path.exists(intervals_file):
            print(f"🔍 Intervals file size: {os.path.getsize(intervals_file)} bytes")
            # Read a bit of the file to verify it's valid JSON
            try:
                with open(intervals_file, 'r', encoding='utf-8') as f:
                    content = f.read(200)  # Read first 200 chars
                    print(f"🔍 Intervals file preview: {content}...")
            except Exception as e:
                print(f"❌ Error reading intervals file: {e}")
        else:
            print(f"❌ Intervals file not found: {intervals_file}")
            # List contents of the temp directory
            temp_contents = os.listdir(temp_dir)
            print(f"🔍 Temp directory contents: {temp_contents}")
        
        # Step 4: Cut video segments
        job.status = "cutting_videos"
        job.message = "Cutting video segments..."
        job.progress = 60
        print(f"🔄 Job {job_id}: {job.message} (Progress: {job.progress}%)")
        
        cutting_success = await run_cut_video_segments(
            intervals_file, video_dir, output_dir, final_video
        )
        
        if not cutting_success:
            raise Exception("Failed to cut video segments")
        
        # Step 5: Read the generated intervals for result
        with open(intervals_file, 'r', encoding='utf-8') as f:
            intervals_data = json.load(f)
        
        # Step 6: Complete
        job.status = "completed"
        job.message = "Video cuts generation completed successfully!"
        job.progress = 100
        
        # Get file size of final video
        final_video_size = os.path.getsize(final_video) if os.path.exists(final_video) else 0
        
        job.result = {
            "final_video_path": final_video,
            "final_video_size": final_video_size,
            "intervals_count": len(intervals_data.get('intervals', [])),
            "total_duration": intervals_data.get('metadata', {}).get('actual_total_duration', 0),
            "output_directory": output_dir,
            "intervals_file": intervals_file,
            "narrative_file": narrative_file
        }
        
        print(f"🎉 Job {job_id} completed successfully!")
        print(f"🎉 Final video: {final_video} ({final_video_size} bytes)")
        print(f"🎉 Intervals: {len(intervals_data.get('intervals', []))}")
        
    except Exception as e:
        error_msg = str(e)
        job.status = "error"
        job.message = f"Error during video cuts generation: {error_msg}"
        job.error = error_msg
        print(f"❌ Job {job_id} failed: {error_msg}")
        print(f"❌ Full error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Error args: {e.args}")
        import traceback
        traceback.print_exc()
        
        # Additional context for debugging
        print(f"🔍 Debug context:")
        print(f"  - Narrative file exists: {os.path.exists(narrative_file) if 'narrative_file' in locals() else 'N/A'}")
        print(f"  - Narrative file size: {os.path.getsize(narrative_file) if 'narrative_file' in locals() and os.path.exists(narrative_file) else 'N/A'}")
        print(f"  - Stream dir exists: {os.path.exists(stream_dir) if 'stream_dir' in locals() else 'N/A'}")
        print(f"  - Video dir exists: {os.path.exists(video_dir) if 'video_dir' in locals() else 'N/A'}")
        print(f"  - Current working directory: {os.getcwd()}")
        print(f"  - Python executable: {sys.executable}")
        print(f"  - Script paths:")
        print(f"    - generate_narrative_intervals.py: {os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'generate_narrative_intervals.py')}")
        print(f"    - cut_video_segments.py: {os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cut_video_segments.py')}")
    
    finally:
        job.completed_at = datetime.now()
        print(f"🏁 Job {job_id} finished at {job.completed_at} with status: {job.status}")

async def run_generate_intervals(narrative_file: str, stream_dir: str, output_file: str, 
                               duration: int, interval_duration: int) -> bool:
    """Run the generate_narrative_intervals.py script."""
    try:
        # Get the path to the script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "generate_narrative_intervals.py")
        
        # Build the command
        cmd = [
            sys.executable, script_path,
            narrative_file,
            "--stream-dir", stream_dir,
            "-o", output_file,
            "--duration", str(duration),
            "--interval-duration", str(interval_duration)
        ]
        
        print(f"🔧 Running command: {' '.join(cmd)}")
        print(f"🔧 Working directory: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        print(f"🔧 Subprocess return code: {result.returncode}")
        print(f"🔧 Subprocess stdout: {result.stdout}")
        print(f"🔧 Subprocess stderr: {result.stderr}")
        
        if result.returncode == 0:
            print(f"✅ Intervals generated successfully: {output_file}")
            # Check if the file was actually created
            if os.path.exists(output_file):
                print(f"✅ Output file exists: {output_file}")
                print(f"✅ Output file size: {os.path.getsize(output_file)} bytes")
            else:
                print(f"⚠️ Warning: Output file not found at expected location: {output_file}")
                # Check if it was created with a different name
                output_dir = os.path.dirname(output_file)
                if os.path.exists(output_dir):
                    files_in_dir = os.listdir(output_dir)
                    json_files = [f for f in files_in_dir if f.endswith('.json')]
                    print(f"🔍 JSON files in output directory: {json_files}")
            return True
        else:
            print(f"❌ Failed to generate intervals")
            print(f"❌ Return code: {result.returncode}")
            print(f"❌ Error output: {result.stderr}")
            print(f"❌ Standard output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Exception running generate_intervals: {e}")
        print(f"❌ Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

async def run_cut_video_segments(intervals_file: str, video_dir: str, output_dir: str, 
                                final_video: str) -> bool:
    """Run the cut_video_segments.py script."""
    try:
        # Get the path to the script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "cut_video_segments.py")
        
        # Debug: Check if intervals file exists
        print(f"🔍 Cut video segments - checking intervals file: {intervals_file}")
        print(f"🔍 Intervals file exists: {os.path.exists(intervals_file)}")
        print(f"🔍 Intervals file absolute path: {os.path.abspath(intervals_file)}")
        
        # Build the command
        cmd = [
            sys.executable, script_path,
            os.path.abspath(intervals_file),  # Use absolute path
            "-v", video_dir,
            "-o", output_dir,
            "-f", final_video
        ]
        
        print(f"🔧 Running command: {' '.join(cmd)}")
        print(f"🔧 Working directory: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
        print(f"🔧 Intervals file absolute path: {os.path.abspath(intervals_file)}")
        
        # Run the command with the same working directory as generate_intervals
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        print(f"🔧 Subprocess return code: {result.returncode}")
        print(f"🔧 Subprocess stdout: {result.stdout}")
        print(f"🔧 Subprocess stderr: {result.stderr}")
        
        if result.returncode == 0:
            print(f"✅ Video segments cut successfully: {final_video}")
            return True
        else:
            print(f"❌ Failed to cut video segments")
            print(f"❌ Return code: {result.returncode}")
            print(f"❌ Error output: {result.stderr}")
            print(f"❌ Standard output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Exception running cut_video_segments: {e}")
        print(f"❌ Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import uvicorn
    print("Starting API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 