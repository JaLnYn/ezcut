#!/usr/bin/env python3
"""
Example usage of the VideoProcessor class
"""

import os
from video_processor import VideoProcessor

def main():
    # Initialize the processor
    # Make sure to set your OPENAI_API_KEY environment variable
    processor = VideoProcessor()
    
    # Example 1: Process a single video (first video from videos folder)
    video_directory = "videos/"
    video_files = [f for f in os.listdir(video_directory) 
                   if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.ts'))]
    
    if video_files:
        video_path = os.path.join(video_directory, video_files[0])
        output_path = f"outputs/{video_files[0]}_single.txt"
        os.makedirs("outputs", exist_ok=True)
        
        print(f"Processing single video: {video_files[0]}...")
        processor.process_video(
            video_path=video_path,
            output_path=output_path,
            keyframe_interval=30,  # Extract keyframes every 30 seconds
            image_prompt="Describe the main action and setting in this video frame"
        )
    else:
        print("No video files found in videos/ directory.")
    
    # Example 2: Process multiple videos in a directory
    video_directory = "videos/"
    output_directory = "outputs/"
    
    if os.path.exists(video_directory):
        print("Processing multiple videos...")
        processor.process_videos(
            video_dir=video_directory,
            output_dir=output_directory,
            keyframe_interval=60,  # Extract keyframes every 60 seconds
            image_prompt="Focus on describing any text, objects, or people visible in the frame"
        )
    else:
        print(f"Video directory {video_directory} not found.")
    
    print("Done! Check the output files for results.")

if __name__ == "__main__":
    main() 