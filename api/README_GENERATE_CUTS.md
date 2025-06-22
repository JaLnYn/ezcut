# Video Cuts Generation API

This API endpoint allows you to generate video cuts from narrative text using the existing video processing pipeline.

## Endpoint

`POST /generate-cuts`

## Request Body

```json
{
  "narrative_text": "Your narrative story here...",
  "duration": 120,
  "interval_duration": 10,
  "job_id": "optional-existing-job-id"
}
```

### Parameters

- `narrative_text` (required): The narrative text to use for generating video intervals
- `duration` (optional, default: 120): Total target duration for the final video in seconds
- `interval_duration` (optional, default: 10): Suggested duration for each individual interval in seconds
- `job_id` (optional): If provided, uses processed files from an existing completed job

## Response

```json
{
  "job_id": "uuid-string",
  "message": "Video cuts generation started.",
  "status_endpoint": "/job/{job_id}"
}
```

## Job Status

Monitor the job progress using the status endpoint:

`GET /job/{job_id}`

### Status Values

- `preparing`: Preparing narrative file
- `generating_intervals`: Generating video intervals from narrative
- `cutting_videos`: Cutting video segments
- `completed`: Job completed successfully
- `error`: Job failed

### Completed Job Result

```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "progress": 100,
  "message": "Video cuts generation completed successfully!",
  "result": {
    "final_video_path": "/path/to/final_cut_video.mp4",
    "final_video_size": 1234567,
    "intervals_count": 12,
    "total_duration": 120.5,
    "output_directory": "/path/to/output_segments",
    "intervals_file": "/path/to/intervals.json",
    "narrative_file": "/path/to/narrative.txt"
  },
  "created_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:05:00"
}
```

## Usage Examples

### Basic Usage

```bash
curl -X POST "http://localhost:8000/generate-cuts" \
  -H "Content-Type: application/json" \
  -d '{
    "narrative_text": "This is a story about developers working on an exciting project...",
    "duration": 60,
    "interval_duration": 5
  }'
```

### Using Existing Job

```bash
curl -X POST "http://localhost:8000/generate-cuts" \
  -H "Content-Type: application/json" \
  -d '{
    "narrative_text": "A different narrative for the same videos...",
    "duration": 90,
    "interval_duration": 8,
    "job_id": "existing-job-uuid"
  }'
```

### JavaScript/TypeScript

```typescript
import { api } from './api/client';

// Generate cuts
const response = await api.generateCuts({
  narrative_text: "Your narrative story here...",
  duration: 120,
  interval_duration: 10
});

// Poll for completion
const pollJob = async (jobId: string) => {
  const status = await api.getJobStatus(jobId);
  
  if (status.status === 'completed') {
    console.log('Final video:', status.result?.final_video_path);
    console.log('Intervals:', status.result?.intervals_count);
  } else if (status.status === 'error') {
    console.error('Error:', status.error);
  } else {
    // Continue polling
    setTimeout(() => pollJob(jobId), 2000);
  }
};

pollJob(response.job_id);
```

## Prerequisites

1. **Processed Video Files**: The API expects processed video files in the `stream_processed_clip` directory
2. **Source Videos**: Original video files should be in the `stream_videos` directory
3. **Scripts**: The `generate_narrative_intervals.py` and `cut_video_segments.py` scripts must be available in the project root

## Directory Structure

```
project/
├── api/
│   └── main.py
├── stream_processed_clip/
│   ├── part1_processed.txt
│   ├── part2_processed.txt
│   └── ...
├── stream_videos/
│   ├── part1.mp4
│   ├── part2.mp4
│   └── ...
├── generate_narrative_intervals.py
└── cut_video_segments.py
```

## Testing

Run the test script to verify the API works:

```bash
cd api
python test_generate_cuts.py
```

## Error Handling

Common errors and solutions:

- **"Failed to generate intervals"**: Check that processed files exist in `stream_processed_clip/`
- **"Failed to cut video segments"**: Check that source videos exist in `stream_videos/`
- **"Job not found"**: The job_id provided doesn't exist or has been deleted
- **"Job is not completed"**: The referenced job hasn't finished processing yet

## Notes

- The API creates temporary directories for processing
- Final video files are saved in temporary locations (consider adding a download endpoint)
- The process uses AI to determine optimal video intervals based on the narrative
- All processing is done asynchronously with progress tracking 