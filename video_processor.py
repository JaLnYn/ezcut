#!/usr/bin/env python3
"""
Video Processor - Extract transcripts and keyframes with AI descriptions
Generates output in format:
[transcript:time] transcript text
[keyframe:time] AI-generated image description
"""

import os
import cv2
import whisper
import argparse
import ffmpeg
from pathlib import Path
from PIL import Image
import base64
import io
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import json
import tempfile

# Load environment variables
load_dotenv()

class VideoProcessor:
    def __init__(self, openai_api_key=None):
        """Initialize the video processor with required models."""
        self.openai_client = OpenAI(api_key=openai_api_key or os.getenv('OPENAI_API_KEY'))
        
        # Load Whisper model (you can change to 'base', 'small', 'medium', 'large')
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        
    def extract_audio(self, video_path, output_path):
        """Extract audio from video file."""
        try:
            (
                ffmpeg
                .input(video_path)
                .output(output_path, acodec='pcm_s16le', ac=1, ar='16k')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return True
        except ffmpeg.Error as e:
            print(f"Error extracting audio: {e}")
            return False
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio using Whisper with timestamps."""
        result = self.whisper_model.transcribe(audio_path, word_timestamps=True)
        return result
    
    def extract_keyframes(self, video_path, interval_seconds=30):
        """Extract keyframes from video at specified intervals."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * interval_seconds)
        
        keyframes = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                keyframes.append({
                    'timestamp': timestamp,
                    'frame': frame
                })
            
            frame_count += 1
        
        cap.release()
        return keyframes
    
    def frame_to_base64(self, frame):
        """Convert OpenCV frame to base64 string."""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        
        # Resize if too large
        if pil_image.width > 1024 or pil_image.height > 1024:
            pil_image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=85)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    
    def describe_image(self, frame, custom_prompt=None):
        """Generate description for keyframe using OpenAI Vision API."""
        base64_image = self.frame_to_base64(frame)
        
        default_prompt = """Describe this video frame in detail. Focus on:
        - Main subjects and actions
        - Setting/environment
        - Key visual elements
        - Mood/atmosphere
        Keep the description concise but informative (2-3 sentences)."""
        
        prompt = custom_prompt or default_prompt
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150
            )
            content = response.choices[0].message.content
            return content.strip() if content else "No description generated"
        except Exception as e:
            print(f"Error describing image: {e}")
            return "Unable to generate description"
    
    def format_timestamp(self, seconds):
        """Convert seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def process_video(self, video_path, output_path, keyframe_interval=30, image_prompt=None):
        """Process a single video file."""
        print(f"Processing video: {video_path}")
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        try:
            # Extract audio
            print("Extracting audio...")
            if not self.extract_audio(video_path, temp_audio_path):
                raise Exception("Failed to extract audio")
            
            # Transcribe audio
            print("Transcribing audio...")
            transcript_result = self.transcribe_audio(temp_audio_path)
            
            # Extract keyframes
            print("Extracting keyframes...")
            keyframes = self.extract_keyframes(video_path, keyframe_interval)
            
            # Generate output
            output_lines = []
            
            # Add transcript with timestamps
            if 'segments' in transcript_result:
                for segment in tqdm(transcript_result['segments'], desc="Processing transcript"):
                    timestamp = self.format_timestamp(segment['start'])
                    text = segment['text'].strip()
                    output_lines.append(f"[transcript:{timestamp}] {text}")
            
            # Add keyframes with AI descriptions
            for keyframe in tqdm(keyframes, desc="Processing keyframes"):
                timestamp = self.format_timestamp(keyframe['timestamp'])
                description = self.describe_image(keyframe['frame'], image_prompt)
                output_lines.append(f"[keyframe:{timestamp}] {description}")
            
            # Sort by timestamp
            def extract_timestamp(line):
                # Extract timestamp from [transcript:HH:MM:SS] or [keyframe:HH:MM:SS]
                timestamp_part = line.split(']')[0]  # Get "[transcript:HH:MM:SS" or "[keyframe:HH:MM:SS"
                timestamp_str = timestamp_part.split(':', 1)[1]  # Get "HH:MM:SS"
                h, m, s = map(int, timestamp_str.split(':'))
                return h * 3600 + m * 60 + s
            
            output_lines.sort(key=extract_timestamp)
            
            # Write output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
            
            print(f"Output saved to: {output_path}")
            
        finally:
            # Clean up temporary audio file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
    
    def process_videos(self, video_dir, output_dir, keyframe_interval=30, image_prompt=None):
        """Process multiple videos in a directory."""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        video_dir = Path(video_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        video_files = [f for f in video_dir.iterdir() 
                      if f.suffix.lower() in video_extensions]
        
        if not video_files:
            print(f"No video files found in {video_dir}")
            return
        
        for video_file in video_files:
            output_file = output_dir / f"{video_file.stem}_processed.txt"
            try:
                self.process_video(str(video_file), str(output_file), 
                                 keyframe_interval, image_prompt)
            except Exception as e:
                print(f"Error processing {video_file}: {e}")
                continue

def main():
    parser = argparse.ArgumentParser(description='Process videos to extract transcripts and keyframes with AI descriptions')
    parser.add_argument('input', help='Input video file or directory containing videos')
    parser.add_argument('-o', '--output', help='Output file or directory', required=True)
    parser.add_argument('-i', '--interval', type=int, default=30, 
                       help='Keyframe extraction interval in seconds (default: 30)')
    parser.add_argument('-p', '--prompt', 
                       help='Custom prompt for image description')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Check if OpenAI API key is available
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OpenAI API key is required. Set OPENAI_API_KEY environment variable or use --api-key")
        return 1
    
    try:
        processor = VideoProcessor(api_key)
        
        input_path = Path(args.input)
        
        if input_path.is_file():
            # Process single video
            processor.process_video(args.input, args.output, args.interval, args.prompt)
        elif input_path.is_dir():
            # Process multiple videos
            processor.process_videos(args.input, args.output, args.interval, args.prompt)
        else:
            print(f"Error: {args.input} is not a valid file or directory")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 