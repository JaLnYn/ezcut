#!/usr/bin/env python3
"""
Vlog Assembler - Create a final vlog video from script and timestamps
Reads vlog_script.txt and cuts/combines videos based on specified timestamps
"""

import os
import re
import ffmpeg
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import subprocess
import tempfile

@dataclass
class VideoSegment:
    """Represents a video segment with timing and metadata"""
    filename: str
    summary: str
    start_time: str
    end_time: Optional[str]
    voiceover: str
    suggested_voiceover: Optional[str] = None

class VlogAssembler:
    def __init__(self, videos_dir: str = "videos", output_dir: str = "outputs"):
        self.videos_dir = Path(videos_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def parse_vlog_script(self, script_path: str) -> List[VideoSegment]:
        """Parse the vlog script file and extract video segments"""
        segments = []
        current_segment = {}
        
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into sections by filename
        sections = re.split(r'\nFilename: ', content)
        
        for section in sections[1:]:  # Skip the first empty section
            lines = section.strip().split('\n')
            if not lines:
                continue
                
            # Extract filename (remove _processed.txt suffix and convert to .mp4)
            filename = lines[0].strip()
            # Convert from processed text filename to video filename
            if filename.endswith('_processed.txt'):
                filename = filename.replace('_processed.txt', '.mp4')
            elif filename.endswith('.TS_processed.txt'):
                filename = filename.replace('_processed.txt', '.mp4')
            elif not filename.endswith('.mp4'):
                filename = filename + '.mp4'
            
            summary = ""
            start_time = "00:00:00"
            end_time = None
            voiceover = ""
            suggested_voiceover = None
            
            # Parse the section content
            for line in lines[1:]:
                line = line.strip()
                if line.startswith('Summary:'):
                    summary = line.replace('Summary:', '').strip()
                elif line.startswith('Transcript start time:'):
                    start_time = line.replace('Transcript start time:', '').strip()
                elif line.startswith('Transcript end time:'):
                    end_time = line.replace('Transcript end time:', '').strip()
                elif line.startswith('Voiceover:'):
                    voiceover = line.replace('Voiceover:', '').strip()
                elif line.startswith('[New script]') and 'Suggest' in line:
                    # Extract suggested voiceover
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        suggested_voiceover = match.group(1)
            
            segment = VideoSegment(
                filename=filename,
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                voiceover=voiceover,
                suggested_voiceover=suggested_voiceover
            )
            segments.append(segment)
        
        return segments
    
    def time_to_seconds(self, time_str: str) -> float:
        """Convert time string (HH:MM:SS) to seconds"""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(float, parts)
                return m * 60 + s
            else:
                return float(parts[0])
        except ValueError:
            return 0.0
    
    def get_video_duration(self, video_path: Path) -> float:
        """Get the duration of a video file in seconds"""
        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['streams'][0]['duration'])
            return duration
        except:
            return 0.0
    
    def cut_video_segment(self, video_path: Path, start_time: str, end_time: Optional[str], output_path: Path) -> bool:
        """Cut a segment from a video file"""
        try:
            start_seconds = self.time_to_seconds(start_time)
            
            # Build ffmpeg input
            input_stream = ffmpeg.input(str(video_path), ss=start_seconds)
            
            # If end time is specified, calculate duration
            if end_time:
                end_seconds = self.time_to_seconds(end_time)
                duration = end_seconds - start_seconds
                if duration > 0:
                    output = ffmpeg.output(input_stream, str(output_path), t=duration, c='copy')
                else:
                    # If duration is 0 or negative, take a short clip (2 seconds)
                    output = ffmpeg.output(input_stream, str(output_path), t=2, c='copy')
            else:
                # If no end time, take the rest of the video (or max 10 seconds for safety)
                video_duration = self.get_video_duration(video_path)
                remaining_duration = min(video_duration - start_seconds, 10)
                if remaining_duration > 0:
                    output = ffmpeg.output(input_stream, str(output_path), t=remaining_duration, c='copy')
                else:
                    output = ffmpeg.output(input_stream, str(output_path), t=2, c='copy')
            
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            return True
            
        except Exception as e:
            print(f"Error cutting video segment {video_path}: {e}")
            return False
    
    def create_concat_file(self, segment_files: List[Path], concat_file_path: Path):
        """Create a concat file for ffmpeg to combine videos"""
        with open(concat_file_path, 'w') as f:
            for segment_file in segment_files:
                f.write(f"file '{segment_file.absolute()}'\n")
    
    def combine_segments(self, segment_files: List[Path], output_path: Path) -> bool:
        """Combine video segments into final video"""
        try:
            # Create temporary concat file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as concat_file:
                concat_file_path = Path(concat_file.name)
                self.create_concat_file(segment_files, concat_file_path)
            
            try:
                # Use ffmpeg to concatenate videos
                cmd = [
                    'ffmpeg', '-f', 'concat', '-safe', '0',
                    '-i', str(concat_file_path),
                    '-c', 'copy',
                    '-y',  # Overwrite output file
                    str(output_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"FFmpeg error: {result.stderr}")
                    return False
                
                return True
                
            finally:
                # Clean up concat file
                concat_file_path.unlink()
                
        except Exception as e:
            print(f"Error combining segments: {e}")
            return False
    
    def assemble_vlog(self, script_path: str, output_filename: str = "final_vlog.mp4") -> bool:
        """Main function to assemble the vlog from script"""
        print("Parsing vlog script...")
        segments = self.parse_vlog_script(script_path)
        
        if not segments:
            print("No segments found in script")
            return False
        
        print(f"Found {len(segments)} video segments")
        
        # Create temporary directory for segments
        temp_dir = self.output_dir / "temp_segments"
        temp_dir.mkdir(exist_ok=True)
        
        segment_files = []
        
        try:
            # Process each segment
            for i, segment in enumerate(segments):
                print(f"Processing segment {i+1}/{len(segments)}: {segment.filename}")
                
                # Find the video file
                video_path = self.videos_dir / segment.filename
                if not video_path.exists():
                    print(f"Warning: Video file not found: {video_path}")
                    continue
                
                # Create output path for this segment
                segment_output = temp_dir / f"segment_{i:03d}_{segment.filename}"
                
                # Cut the video segment
                if self.cut_video_segment(video_path, segment.start_time, segment.end_time, segment_output):
                    segment_files.append(segment_output)
                    print(f"  ✓ Cut segment: {segment.start_time} - {segment.end_time or 'end'}")
                else:
                    print(f"  ✗ Failed to cut segment from {segment.filename}")
            
            if not segment_files:
                print("No segments were successfully processed")
                return False
            
            # Combine all segments
            final_output = self.output_dir / output_filename
            print(f"\nCombining {len(segment_files)} segments into final video...")
            
            if self.combine_segments(segment_files, final_output):
                print(f"✓ Final vlog created: {final_output}")
                
                # Print summary
                print(f"\nVlog Summary:")
                print(f"- Total segments: {len(segment_files)}")
                print(f"- Output file: {final_output}")
                print(f"- File size: {final_output.stat().st_size / (1024*1024):.1f} MB")
                
                return True
            else:
                print("✗ Failed to combine segments")
                return False
                
        finally:
            # Clean up temporary segment files
            for segment_file in segment_files:
                if segment_file.exists():
                    segment_file.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()
    
    def create_script_summary(self, script_path: str, output_path: str = None):
        """Create a readable summary of the vlog script"""
        segments = self.parse_vlog_script(script_path)
        
        if output_path is None:
            output_path = self.output_dir / "vlog_summary.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("VLOG ASSEMBLY SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            total_duration = 0
            
            for i, segment in enumerate(segments, 1):
                f.write(f"Segment {i}: {segment.filename}\n")
                f.write(f"Summary: {segment.summary}\n")
                f.write(f"Time: {segment.start_time}")
                if segment.end_time:
                    f.write(f" - {segment.end_time}")
                    duration = self.time_to_seconds(segment.end_time) - self.time_to_seconds(segment.start_time)
                    f.write(f" (Duration: {duration:.1f}s)")
                    total_duration += duration
                f.write(f"\n")
                
                if segment.suggested_voiceover:
                    f.write(f"Suggested Voiceover: {segment.suggested_voiceover}\n")
                else:
                    f.write(f"Original Audio: {segment.voiceover[:100]}{'...' if len(segment.voiceover) > 100 else ''}\n")
                
                f.write("-" * 40 + "\n\n")
            
            f.write(f"Estimated total duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)\n")
        
        print(f"Script summary created: {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Assemble vlog from script and video segments")
    parser.add_argument("script", help="Path to vlog script file")
    parser.add_argument("-o", "--output", default="final_vlog.mp4", help="Output filename")
    parser.add_argument("-v", "--videos-dir", default="videos", help="Directory containing video files")
    parser.add_argument("--summary-only", action="store_true", help="Only create script summary, don't process videos")
    
    args = parser.parse_args()
    
    assembler = VlogAssembler(videos_dir=args.videos_dir)
    
    if args.summary_only:
        assembler.create_script_summary(args.script)
    else:
        success = assembler.assemble_vlog(args.script, args.output)
        if not success:
            exit(1)

if __name__ == "__main__":
    main() 