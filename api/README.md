# Video Processing & Narrative Generation API

A FastAPI application that processes uploaded videos using AI to extract transcripts and keyframes, then generates engaging narratives.

## Features

- **Multi-video upload**: Upload multiple video files simultaneously
- **AI-powered processing**: Uses Whisper for transcription and CLIP for intelligent keyframe selection
- **Narrative generation**: Creates engaging summaries using OpenAI GPT-4
- **Async processing**: Background job processing with real-time status updates
- **RESTful API**: Clean REST endpoints with automatic documentation

## Setup

1. **Install dependencies**:

```bash
# From the project root directory
pip install -r requirements.txt
```

2. **Set environment variables**:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

3. **Start the server**:

```bash
python api/main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check

```bash
GET /health
```

### Upload Videos

```bash
POST /upload-videos
Content-Type: multipart/form-data

files: video1.mp4
files: video2.mp4
...
```

**Response**:

```json
{
  "job_id": "uuid-string",
  "message": "Uploaded 2 videos. Processing started.",
  "status_endpoint": "/job/uuid-string"
}
```

### Check Job Status

```bash
GET /job/{job_id}
```

**Response**:

```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "progress": 100,
  "message": "Processing completed successfully!",
  "result": {
    "narrative": "Generated narrative text...",
    "output_file": "api_outputs/narrative_20241220_143022.txt",
    "processed_files": 2
  },
  "created_at": "2024-12-20T14:30:22",
  "completed_at": "2024-12-20T14:35:45"
}
```

### List All Jobs

```bash
GET /jobs
```

### Delete Job

```bash
DELETE /job/{job_id}
```

### Clear All Jobs

```bash
DELETE /jobs
```

## Job Statuses

- `uploading`: Files are being uploaded and saved
- `processing`: Videos are being processed with AI
- `generating_narrative`: Creating narrative from processed content
- `completed`: Processing finished successfully
- `error`: An error occurred during processing

## Usage Examples

### Using curl

```bash
# Upload videos
curl -X POST http://localhost:8000/upload-videos \
  -F 'files=@video1.mp4' \
  -F 'files=@video2.mp4'

# Check status
curl http://localhost:8000/job/{job_id}

# List all jobs
curl http://localhost:8000/jobs
```

### Using Python

```python
import requests

# Upload videos
files = [
    ('files', open('video1.mp4', 'rb')),
    ('files', open('video2.mp4', 'rb'))
]
response = requests.post('http://localhost:8000/upload-videos', files=files)
job_id = response.json()['job_id']

# Monitor progress
while True:
    status = requests.get(f'http://localhost:8000/job/{job_id}').json()
    print(f"Status: {status['status']} - {status['progress']}%")

    if status['status'] in ['completed', 'error']:
        if status['status'] == 'completed':
            print("Narrative:", status['result']['narrative'])
        break

    time.sleep(5)
```

### Using the test script

```bash
python api/test_api.py
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Output

- **Processed files**: Each video generates a `{filename}_processed.txt` file with transcripts and keyframes
- **Narrative**: Generated narrative saved to `api_outputs/narrative_TIMESTAMP.txt`
- **Job tracking**: Real-time status updates via API endpoints

## Supported Video Formats

- MP4, AVI, MOV, MKV, WMV, FLV, WebM

## Architecture

1. **Upload**: Videos are saved to temporary directory
2. **Processing**: Each video is processed using `video_processor.py`
3. **Narrative Generation**: Combined processed content is sent to `nlpv2` for narrative generation
4. **Cleanup**: Temporary files are automatically removed
5. **Status Tracking**: Real-time progress updates via job status endpoints

## Error Handling

- Invalid file types are rejected
- Processing errors are captured and reported
- Temporary files are cleaned up even if errors occur
- Detailed error messages in job status

## Performance

- **Async processing**: Videos are processed in the background
- **Memory efficient**: Files are processed one at a time
- **Scalable**: Can handle multiple concurrent uploads
- **Progress tracking**: Real-time status updates
