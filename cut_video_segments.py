#!/usr/bin/env python3
"""
Script to cut video segments from the JSON intervals file using ffmpeg
"""

import json
import subprocess
import os
import sys
from pathlib import Path

def time_to_seconds(time_str):
    """Convert time string (HH:MM:SS) to seconds"""
    parts = time_str.split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

def run_ffmpeg_command(command):
    """Run an ffmpeg command and handle errors"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {command}")
            print(f"Error output: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running command: {command}")
        print(f"Exception: {e}")
        return False

def cut_video_segments(json_file_path, source_video_dir="stream_videos", output_dir="output_segments", final_output="final_cut_video.mp4"):
    """
    Cut video segments based on the JSON intervals file
    """
    
    # Read the JSON file
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return False
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # List to store segment file paths for concatenation
    segment_files = []
    
    # Process each interval
    intervals = data.get('intervals', [])
    print(f"Processing {len(intervals)} intervals...")
    
    for interval in intervals:
        index = interval['index']
        start_time = interval['start_time']
        end_time = interval['end_time']
        source_video = interval['source_video']
        
        # Construct paths
        source_path = os.path.join(source_video_dir, f"{source_video}.mp4")
        output_filename = f"segment_{index:02d}_{source_video}_{start_time.replace(':', '')}-{end_time.replace(':', '')}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        # Check if source video exists
        if not os.path.exists(source_path):
            print(f"Warning: Source video not found: {source_path}")
            continue
        
        print(f"Cutting segment {index}: {source_video} from {start_time} to {end_time}")
        
        # ffmpeg command to cut the segment
        # Using -ss for start time, -to for end time, -c copy for fast copying without re-encoding
        command = f'ffmpeg -i "{source_path}" -ss {start_time} -to {end_time} "{output_path}" -y'
        
        if run_ffmpeg_command(command):
            segment_files.append(output_path)
            print(f"✓ Created segment: {output_filename}")
        else:
            print(f"✗ Failed to create segment: {output_filename}")
    
    if not segment_files:
        print("No segments were created successfully.")
        return False
    
    # Create concatenation file list
    concat_file_path = os.path.join(output_dir, "segments_list.txt")
    with open(concat_file_path, 'w') as f:
        for segment_file in segment_files:
            f.write(f"file '{os.path.abspath(segment_file)}'\n")
    
    # Use the provided final output filename
    
    print(f"\nConcatenating {len(segment_files)} segments into final video...")
    
    # ffmpeg command to concatenate all segments
    concat_command = f'ffmpeg -f concat -safe 0 -i "{concat_file_path}" -c copy "{final_output}" -y'
    
    if run_ffmpeg_command(concat_command):
        print(f"✓ Final video created: {final_output}")
        
        # Get metadata from JSON
        metadata = data.get('metadata', {})
        total_duration = metadata.get('actual_total_duration', 0)
        total_intervals = metadata.get('total_intervals', len(intervals))
        
        print(f"\nSummary:")
        print(f"- Total intervals processed: {total_intervals}")
        print(f"- Expected total duration: {total_duration} seconds")
        print(f"- Output video: {final_output}")
        print(f"- Segment files saved in: {output_dir}")
        
        return True
    else:
        print("✗ Failed to create final concatenated video")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cut video segments based on JSON intervals file')
    parser.add_argument('json_file', nargs='?', default='stream_processed_clip_intervals_v3.json',
                       help='Path to the JSON intervals file (default: stream_processed_clip_intervals_v3.json)')
    parser.add_argument('--video-dir', '-v', default='stream_videos',
                       help='Directory containing source video files (default: stream_videos)')
    parser.add_argument('--output-dir', '-o', default='output_segments',
                       help='Directory to save output segments (default: output_segments)')
    parser.add_argument('--final-output', '-f', default='final_cut_video.mp4',
                       help='Final output video filename (default: final_cut_video.mp4)')
    
    args = parser.parse_args()
    
    json_file = args.json_file
    video_dir = args.video_dir
    output_dir = args.output_dir
    final_output = args.final_output
    
    if not os.path.exists(json_file):
        print(f"Error: JSON file not found: {json_file}")
        print("\nUsage examples:")
        print("  python cut_video_segments.py")
        print("  python cut_video_segments.py my_intervals.json")
        print("  python cut_video_segments.py my_intervals.json --video-dir /path/to/videos")
        print("  python cut_video_segments.py my_intervals.json -v /path/to/videos -o /path/to/output")
        print("  python cut_video_segments.py my_intervals.json -v /path/to/videos -f my_final_video.mp4")
        sys.exit(1)
    
    if not os.path.exists(video_dir):
        print(f"Error: Video directory not found: {video_dir}")
        sys.exit(1)
    
    print(f"Processing intervals from: {json_file}")
    print(f"Source video directory: {video_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Final output file: {final_output}")
    print("=" * 60)
    
    success = cut_video_segments(json_file, video_dir, output_dir, final_output)
    
    if success:
        print("\n🎉 Video cutting and concatenation completed successfully!")
    else:
        print("\n❌ Video processing failed.")
        sys.exit(1)

if __name__ == "__main__":
    main() 