# EZCut - Video Processing Pipeline

A powerful video processing tool that generates transcripts with timestamps and keyframes with AI-generated descriptions.

## Features

- **Automatic Speech Recognition**: Extract transcripts with precise timestamps using OpenAI Whisper
- **Keyframe Extraction**: Extract frames at regular intervals from videos
- **AI-Powered Image Descriptions**: Generate detailed descriptions of keyframes using OpenAI's GPT-4 Vision
- **Batch Processing**: Process multiple videos at once
- **Flexible Output Format**: Generate structured output with timestamps

## Output Format

The tool generates output in this format:
```
[transcript:00:00:15] Hello, welcome to our video presentation
[keyframe:00:00:30] A professional speaker standing at a podium in a modern conference room with a large screen displaying charts
[transcript:00:00:45] Today we'll be discussing the latest trends in technology
[keyframe:00:01:00] Close-up shot of hands typing on a laptop keyboard with code visible on the screen
```

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install FFmpeg** (required for audio extraction):
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

3. **Set up OpenAI API Key:**
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Usage

### Quick Start - Process all videos in videos/ folder:
```bash
python process_videos.py
```

### Process a single video:
```bash
python video_processor.py videos/your_video.mp4 -o outputs/output.txt
```

### Process all videos in the videos directory:
```bash
python video_processor.py videos/ -o outputs/
```

### Advanced options:
```bash
# Custom keyframe interval (every 60 seconds)
python video_processor.py video.mp4 -o output.txt -i 60

# Custom image description prompt
python video_processor.py video.mp4 -o output.txt -p "Describe what products are visible in this frame"

# Use API key directly
python video_processor.py video.mp4 -o output.txt --api-key sk-your-key-here
```

## Configuration Options

- `-i, --interval`: Keyframe extraction interval in seconds (default: 30)
- `-p, --prompt`: Custom prompt for AI image descriptions
- `--api-key`: OpenAI API key (alternatively set OPENAI_API_KEY environment variable)

## Supported Video Formats

- MP4, AVI, MOV, MKV, WMV, FLV, WebM

## Requirements

- Python 3.8+
- OpenAI API key with GPT-4 Vision access
- FFmpeg for audio processing
- Sufficient disk space for temporary audio files

## Cost Considerations

- **Whisper**: Free (runs locally)
- **GPT-4 Vision**: ~$0.01-0.03 per image depending on detail level
- For a 10-minute video with 30-second keyframe intervals, expect ~20 API calls

## Troubleshooting

### Common Issues:

1. **"FFmpeg not found"**: Install FFmpeg and ensure it's in your PATH
2. **"OpenAI API key missing"**: Set up your API key in `.env` file or use `--api-key`
3. **"Out of memory"**: Use smaller Whisper model in code (change to 'tiny' or 'base')
4. **"GPU errors"**: The tool works on CPU, no GPU required

### Performance Tips:

- Use `base` Whisper model for good balance of speed/accuracy
- Increase keyframe interval for longer videos to reduce API costs
- Process videos in smaller batches if you have many files
