#!/usr/bin/env python3
"""
Simple script to process all videos in the videos/ folder
"""

import os
from pathlib import Path
from video_processor import VideoProcessor

def main():
    # Set up paths
    videos_dir = "videos"
    outputs_dir = "outputs"
    
    # Create outputs directory if it doesn't exist
    Path(outputs_dir).mkdir(exist_ok=True)
    
    # Check if videos directory exists
    if not os.path.exists(videos_dir):
        print(f"Error: {videos_dir} directory not found!")
        print("Please create a 'videos' folder and add your video files to it.")
        return 1
    
    # Count video files
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.ts'}
    video_files = [f for f in Path(videos_dir).iterdir() 
                   if f.suffix.lower() in video_extensions]
    
    if not video_files:
        print(f"No video files found in {videos_dir} directory!")
        return 1
    
    print(f"Found {len(video_files)} video files to process:")
    for video_file in video_files:
        print(f"  - {video_file.name}")
    
    # Initialize the processor
    print("\nInitializing video processor...")
    try:
        processor = VideoProcessor()
    except Exception as e:
        print(f"Error initializing processor: {e}")
        print("Make sure you have set your OPENAI_API_KEY environment variable.")
        return 1
    
    # Process all videos
    print(f"\nProcessing videos...")
    processor.process_videos(
        video_dir=videos_dir,
        output_dir=outputs_dir,
        keyframe_interval=30,  # Extract keyframes every 30 seconds
        image_prompt="Describe this video frame in detail, focusing on the main subjects, actions, setting, and any notable visual elements."
    )
    
    print(f"\n✅ Processing complete! Check the '{outputs_dir}' folder for results.")
    
    # List output files
    output_files = list(Path(outputs_dir).glob("*.txt"))
    if output_files:
        print(f"\nGenerated {len(output_files)} output files:")
        for output_file in output_files:
            print(f"  - {output_file.name}")
    
    return 0

if __name__ == "__main__":
    exit(main()) 