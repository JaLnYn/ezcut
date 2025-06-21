#!/usr/bin/env python3
"""
Script to cut videos based on transcript timings and concatenate them into a final vlog.
"""

import os
import re
import ffmpeg
from pathlib import Path
from typing import List, Dict, Tuple

class VideoCutter:
    def __init__(self, videos_dir: str = "videos", output_dir: str = "cut_videos"):
        self.videos_dir = Path(videos_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def parse_vlog_story(self, story_file: str = "vlog_story.txt") -> List[Dict]:
        """Parse the vlog story file to extract video information and timings."""
        entries = []
        
        with open(story_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by filename entries
        sections = re.split(r'Filename: ', content)[1:]  # Skip first empty section
        
        for section in sections:
            lines = section.strip().split('\n')
            if not lines:
                continue
                
            filename = lines[0].strip()
            
            # Extract timing information
            start_time = None
            end_time = None
            
            for line in lines:
                if line.startswith('Transcript start time:'):
                    start_time = line.split(':', 1)[1].strip()
                elif line.startswith('Transcript end time:'):
                    end_time = line.split(':', 1)[1].strip()
            
            entries.append({
                'filename': filename,
                'start_time': start_time,
                'end_time': end_time
            })
        
        return entries
    
    def time_to_seconds(self, time_str: str) -> float:
        """Convert time string (HH:MM:SS) to seconds."""
        if not time_str:
            return 0.0
        
        parts = time_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
        else:
            return float(time_str)
    
    def cut_video(self, input_file: Path, output_file: Path, start_time: str, end_time: str) -> bool:
        """Cut a video segment using ffmpeg-python."""
        try:
            start_sec = self.time_to_seconds(start_time)
            
            # Load the input video
            input_stream = ffmpeg.input(str(input_file))
            
            # Calculate duration if end time is specified
            duration = None
            if end_time:
                end_sec = self.time_to_seconds(end_time)
                duration = end_sec - start_sec
            
            # Build output with start time and duration
            output_args = {
                'ss': start_sec,
                'acodec': 'copy',
                'vcodec': 'copy',
                'avoid_negative_ts': 'make_zero'
            }
            
            if duration:
                output_args['t'] = duration
            
            output = ffmpeg.output(input_stream, str(output_file), **output_args)
            
            # Run the ffmpeg command
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            print(f"✓ Cut {input_file.name} -> {output_file.name}")
            return True
            
        except ffmpeg.Error as e:
            print(f"✗ Error cutting {input_file.name}: {e}")
            if e.stderr:
                print(f"ffmpeg stderr: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error cutting {input_file.name}: {e}")
            return False
    
    def create_concat_file(self, cut_videos: List[Path]) -> Path:
        """Create a concat file for ffmpeg."""
        concat_file = self.output_dir / "concat_list.txt"
        
        with open(concat_file, 'w') as f:
            for video in cut_videos:
                f.write(f"file '{video.absolute()}'\n")
        
        return concat_file
    
    def concatenate_videos(self, concat_file: Path, output_file: Path) -> bool:
        """Concatenate videos using ffmpeg-python."""
        try:
            # Use concat demuxer
            input_stream = ffmpeg.input(str(concat_file), f='concat', safe=0)
            
            output = ffmpeg.output(
                input_stream,
                str(output_file),
                acodec='copy',
                vcodec='copy'
            )
            
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            print(f"✓ Concatenated videos -> {output_file}")
            return True
            
        except ffmpeg.Error as e:
            print(f"✗ Error concatenating videos: {e}")
            if e.stderr:
                print(f"ffmpeg stderr: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error concatenating videos: {e}")
            return False
    
    def process_videos(self) -> bool:
        """Main processing function."""
        print("🎬 Starting video cutting and concatenation process...")
        
        # Parse the vlog story
        entries = self.parse_vlog_story()
        print(f"📝 Found {len(entries)} video entries in vlog story")
        
        cut_videos = []
        
        # Process each video entry
        for i, entry in enumerate(entries):
            filename = entry['filename']
            start_time = entry['start_time']
            end_time = entry['end_time']
            
            # Convert filename from _processed.txt to .mp4
            # Remove _processed.txt and add .mp4
            base_filename = filename.replace('_processed.txt', '')
            video_file = self.videos_dir / f"{base_filename}.mp4"
            
            if not video_file.exists():
                print(f"⚠️  Video file not found: {video_file}")
                continue
            
            # Create output filename
            output_filename = f"cut_{i:02d}_{video_file.stem}.mp4"
            output_file = self.output_dir / output_filename
            
            print(f"\n🎥 Processing {video_file.name}")
            print(f"   Start: {start_time or '0:00:00'}")
            print(f"   End: {end_time or 'full video'}")
            
            # Cut the video
            if self.cut_video(video_file, output_file, start_time, end_time):
                cut_videos.append(output_file)
        
        if not cut_videos:
            print("❌ No videos were successfully cut!")
            return False
        
        # Create concat file
        concat_file = self.create_concat_file(cut_videos)
        
        # Concatenate all cut videos
        final_output = Path("final_vlog.mp4")
        success = self.concatenate_videos(concat_file, final_output)
        
        if success:
            print(f"\n🎉 Success! Final vlog created: {final_output}")
            print(f"📁 Cut videos saved in: {self.output_dir}")
        else:
            print("\n❌ Failed to create final vlog")
        
        return success

def main():
    """Main function."""
    # Check if ffmpeg-python is available
    try:
        import ffmpeg
        print("✓ ffmpeg-python is available")
    except ImportError:
        print("❌ ffmpeg-python is not installed")
        print("Please install it: pip install ffmpeg-python")
        return
    
    # Process videos
    cutter = VideoCutter()
    success = cutter.process_videos()
    
    if success:
        print("\n✨ Video processing completed successfully!")
    else:
        print("\n💥 Video processing failed!")

if __name__ == "__main__":
    main() 