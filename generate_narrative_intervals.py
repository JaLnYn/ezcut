#!/usr/bin/env python3
"""
Script to generate dynamic timestamp intervals from narrative text and processed stream data.
Uses OpenAI API to determine natural story breaks and generate descriptions.
"""

import os
import json
import argparse
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class TimestampEntry:
    timestamp: str
    entry_type: str  # 'transcript' or 'keyframe'
    content: str
    source_video: str  # Which part video this comes from (e.g., "part1", "part2")
    speaker: Optional[str] = None

@dataclass
class TimeInterval:
    start_time: str
    end_time: str
    duration_seconds: float
    ai_description: str
    source_video: str  # Which part video to cut from

class NarrativeIntervalGenerator:
    def __init__(self, narrative_file: str, stream_dir: str, total_duration: int = 60, suggested_interval_duration: int = 5):
        self.narrative_file = narrative_file
        self.stream_dir = stream_dir
        self.total_duration = total_duration  # Total target duration for entire video
        self.suggested_interval_duration = suggested_interval_duration  # Suggested duration for each interval
        self.min_interval_duration = max(1, suggested_interval_duration - 2)  # Minimum is 2s less than suggested, but at least 1s
        self.max_interval_duration = suggested_interval_duration + 2  # Maximum is 2s more than suggested
        self.openai_client: openai.OpenAI = self._setup_openai()
        
    def _setup_openai(self) -> openai.OpenAI:
        """Initialize OpenAI client with API key from environment"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return openai.OpenAI(api_key=api_key)
    
    def parse_timestamp(self, timestamp_str: str) -> float:
        """Convert timestamp string (HH:MM:SS) to seconds"""
        try:
            parts = timestamp_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
            else:
                return float(parts[0])
        except:
            return 0.0
    
    def seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def read_narrative(self) -> str:
        """Read the narrative text file"""
        with open(self.narrative_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    def extract_part_name(self, filename: str) -> str:
        """Extract part name from filename (e.g., 'part1_processed.txt' -> 'part1')"""
        basename = os.path.basename(filename)
        if '_processed.txt' in basename:
            return basename.replace('_processed.txt', '')
        elif '.txt' in basename:
            return basename.replace('.txt', '')
        return basename
    
    def parse_stream_file(self, filepath: str) -> List[TimestampEntry]:
        """Parse a single processed stream file"""
        entries = []
        source_video = self.extract_part_name(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse transcript entries
        transcript_pattern = r'\[transcript:(\d{2}:\d{2}:\d{2})\]\s*([^\n]*?)(?:\n|$)'
        for match in re.finditer(transcript_pattern, content):
            timestamp, text = match.groups()
            speaker = None
            
            # Check if there's a speaker name at the beginning
            text = text.strip()
            if text and not text.startswith('[') and len(text.split()) > 0:
                first_word = text.split()[0]
                if first_word and first_word[0].isupper() and len(first_word) < 20:
                    # Likely a speaker name
                    words = text.split(' ', 1)
                    if len(words) > 1:
                        speaker = words[0]
                        text = words[1]
            
            if text:  # Only add non-empty entries
                entries.append(TimestampEntry(timestamp, 'transcript', text, source_video, speaker))
        
        # Parse keyframe entries
        keyframe_pattern = r'\[keyframe:(\d{2}:\d{2}:\d{2})\]\s*([^\n]*?)(?:\n|$)'
        for match in re.finditer(keyframe_pattern, content):
            timestamp, description = match.groups()
            if description.strip():
                entries.append(TimestampEntry(timestamp, 'keyframe', description.strip(), source_video))
        
        return entries
    
    def read_all_stream_files(self) -> List[TimestampEntry]:
        """Read and parse all processed stream files"""
        all_entries = []
        
        if not os.path.exists(self.stream_dir):
            raise FileNotFoundError(f"Stream directory not found: {self.stream_dir}")
        
        # Get all processed files
        files = [f for f in os.listdir(self.stream_dir) if f.endswith('_processed.txt')]
        files.sort()  # Sort to ensure consistent order
        
        print(f"Found processed files: {files}")
        
        for filename in files:
            filepath = os.path.join(self.stream_dir, filename)
            entries = self.parse_stream_file(filepath)
            all_entries.extend(entries)
            print(f"Loaded {len(entries)} entries from {filename}")
        
        # Sort all entries by timestamp within each source video
        # Note: We assume timestamps reset for each part, so we don't sort globally
        return all_entries
    
    def group_entries_by_video(self, entries: List[TimestampEntry]) -> Dict[str, List[TimestampEntry]]:
        """Group entries by source video"""
        video_groups = {}
        for entry in entries:
            if entry.source_video not in video_groups:
                video_groups[entry.source_video] = []
            video_groups[entry.source_video].append(entry)
        
        # Sort entries within each video by timestamp
        for video, video_entries in video_groups.items():
            video_entries.sort(key=lambda x: self.parse_timestamp(x.timestamp))
        
        return video_groups
    
    def get_ai_interval_suggestions(self, video_groups: Dict[str, List[TimestampEntry]], narrative: str) -> List[TimeInterval]:
        """Use AI to determine optimal intervals that fit within target duration"""
        print("Analyzing content for optimal intervals within target duration...")
        
        # Calculate total available content duration
        total_available_duration = 0
        video_durations = {}
        
        for video, entries in video_groups.items():
            if entries:
                duration = self.parse_timestamp(entries[-1].timestamp)
                video_durations[video] = duration
                total_available_duration += duration
        
        print(f"Total available content: {total_available_duration:.1f}s, Target: {self.total_duration}s")
        
        # Calculate selection ratio (how much content we need vs. available)
        selection_ratio = min(1.0, self.total_duration / total_available_duration) if total_available_duration > 0 else 0
        
        all_intervals = []
        
        for video, entries in video_groups.items():
            if not entries:
                continue
                
            print(f"Analyzing {video} with {len(entries)} entries...")
            
            # Create a condensed version for AI analysis
            content_chunks = []
            current_chunk = []
            chunk_duration = 15  # Smaller chunks for better granularity
            
            chunk_start = self.parse_timestamp(entries[0].timestamp)
            
            for entry in entries:
                entry_time = self.parse_timestamp(entry.timestamp)
                
                if entry_time - chunk_start >= chunk_duration:
                    if current_chunk:
                        # Summarize this chunk
                        chunk_content = []
                        for e in current_chunk:
                            if e.entry_type == 'transcript' and e.content:
                                speaker_prefix = f"{e.speaker}: " if e.speaker else ""
                                chunk_content.append(f"{speaker_prefix}{e.content}")
                            elif e.entry_type == 'keyframe':
                                chunk_content.append(f"[Visual: {e.content[:50]}...]")
                        
                        chunk_summary = " | ".join(chunk_content[:3])
                        content_chunks.append({
                            'timestamp': self.seconds_to_timestamp(chunk_start),
                            'timestamp_seconds': chunk_start,
                            'content': chunk_summary,
                            'duration': entry_time - chunk_start
                        })
                    
                    chunk_start = entry_time
                    current_chunk = [entry]
                else:
                    current_chunk.append(entry)
            
            # Add final chunk
            if current_chunk:
                chunk_content = []
                for e in current_chunk:
                    if e.entry_type == 'transcript' and e.content:
                        speaker_prefix = f"{e.speaker}: " if e.speaker else ""
                        chunk_content.append(f"{speaker_prefix}{e.content}")
                    elif e.entry_type == 'keyframe':
                        chunk_content.append(f"[Visual: {e.content[:50]}...]")
                
                chunk_summary = " | ".join(chunk_content[:3])
                final_duration = self.parse_timestamp(entries[-1].timestamp) - chunk_start
                content_chunks.append({
                    'timestamp': self.seconds_to_timestamp(chunk_start),
                    'timestamp_seconds': chunk_start,
                    'content': chunk_summary,
                    'duration': final_duration
                })
            
            # Calculate target duration for this video proportionally
            video_target_duration = video_durations[video] * selection_ratio
            
            # Prepare content for AI analysis
            content_for_ai = "\n".join([
                f"{chunk['timestamp']} ({chunk['duration']:.1f}s): {chunk['content']}" 
                for chunk in content_chunks
            ])
            
            try:
                prompt = f"""
Based on this narrative story:
"{narrative[:400]}"

I need to select the BEST {video_target_duration:.1f} seconds of content from video "{video}" (out of {video_durations[video]:.1f}s available).

Content with timestamps and durations:
{content_for_ai[:2000]}...

CONSTRAINTS:
- Total selected duration must be approximately {video_target_duration:.1f} seconds
- Each interval should be {self.min_interval_duration}-{self.suggested_interval_duration} seconds long (no longer than {self.max_interval_duration}s!)
- Select the most engaging, story-relevant, or emotionally impactful moments
- Prioritize quality over quantity

Please select the best intervals that fit these constraints. Return ONLY a JSON array of objects like:
[
  {{"start": "00:01:30", "end": "00:01:45", "reason": "Key dialogue/moment"}},
  {{"start": "00:03:20", "end": "00:03:35", "reason": "Important visual/reaction"}}
]
"""
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",  # Use GPT-4 for better reasoning about constraints
                    messages=[
                        {"role": "system", "content": "You are a video editor expert at selecting the best moments from content. You must respect duration constraints strictly. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=600,
                    temperature=0.3
                )
                
                ai_response = response.choices[0].message.content
                if ai_response:
                    try:
                        # Extract JSON from response
                        start_idx = ai_response.find('[')
                        end_idx = ai_response.rfind(']') + 1
                        if start_idx != -1 and end_idx > start_idx:
                            json_str = ai_response[start_idx:end_idx]
                            suggested_intervals = json.loads(json_str)
                            
                            for interval_data in suggested_intervals:
                                if isinstance(interval_data, dict) and 'start' in interval_data and 'end' in interval_data:
                                    start_seconds = self.parse_timestamp(interval_data['start'])
                                    end_seconds = self.parse_timestamp(interval_data['end'])
                                    duration = end_seconds - start_seconds
                                    
                                    # Enforce max duration
                                    if duration > self.max_interval_duration:
                                        end_seconds = start_seconds + self.max_interval_duration
                                        duration = self.max_interval_duration
                                    
                                    # Enforce min duration
                                    if duration < self.min_interval_duration:
                                        continue
                                    
                                    interval = TimeInterval(
                                        start_time=self.seconds_to_timestamp(start_seconds),
                                        end_time=self.seconds_to_timestamp(end_seconds),
                                        duration_seconds=duration,
                                        ai_description=interval_data.get('reason', ''),
                                        source_video=video
                                    )
                                    all_intervals.append(interval)
                            
                            print(f"AI selected {len([i for i in all_intervals if i.source_video == video])} intervals for {video}")
                            continue
                    except Exception as e:
                        print(f"Failed to parse AI response for {video}: {e}")
            
            except Exception as e:
                print(f"Error getting AI suggestions for {video}: {e}")
            
            # Fallback: select best moments manually
            if video_target_duration > 0:
                # Calculate intervals based on suggested duration
                num_intervals = max(1, int(video_target_duration / self.suggested_interval_duration))
                if num_intervals > 0:
                    video_duration = video_durations[video]
                    interval_size = min(self.max_interval_duration, max(self.min_interval_duration, video_target_duration / num_intervals))
                    
                    # Select evenly distributed intervals
                    for i in range(num_intervals):
                        start_time = (video_duration / num_intervals) * i
                        end_time = min(start_time + interval_size, video_duration)
                        
                        if end_time - start_time >= self.min_interval_duration:
                            interval = TimeInterval(
                                start_time=self.seconds_to_timestamp(start_time),
                                end_time=self.seconds_to_timestamp(end_time),
                                duration_seconds=end_time - start_time,
                                ai_description=f"Selected segment from {video}",
                                source_video=video
                            )
                            all_intervals.append(interval)
        
        # Sort all intervals and trim to fit target duration if needed
        all_intervals.sort(key=lambda x: (x.source_video, self.parse_timestamp(x.start_time)))
        
        # Ensure we don't exceed target duration
        total_selected_duration = sum(i.duration_seconds for i in all_intervals)
        if total_selected_duration > self.total_duration:
            print(f"Selected {total_selected_duration:.1f}s, trimming to {self.total_duration}s...")
            # Remove intervals until we fit the target
            running_total = 0
            filtered_intervals = []
            for interval in all_intervals:
                if running_total + interval.duration_seconds <= self.total_duration:
                    filtered_intervals.append(interval)
                    running_total += interval.duration_seconds
                else:
                    break
            all_intervals = filtered_intervals
        
        return all_intervals
    
    def create_intervals(self, entries: List[TimestampEntry], narrative: str) -> List[TimeInterval]:
        """Create time intervals based on AI-suggested selections that fit target duration"""
        if not entries:
            return []
        
        # Group entries by video
        video_groups = self.group_entries_by_video(entries)
        
        # Get AI suggestions for optimal intervals within target duration
        all_intervals = self.get_ai_interval_suggestions(video_groups, narrative)
        
        print(f"Created {len(all_intervals)} total intervals")
        
        return all_intervals
    
    def generate_ai_descriptions(self, intervals: List[TimeInterval], entries: List[TimestampEntry], narrative: str) -> List[TimeInterval]:
        """Generate enhanced AI descriptions for intervals that don't already have good descriptions"""
        print("Enhancing AI descriptions for intervals...")
        
        for i, interval in enumerate(intervals):
            # Skip if already has a good AI description from the selection process
            if interval.ai_description and len(interval.ai_description) > 10 and not interval.ai_description.startswith("Selected segment"):
                print(f"Keeping existing description for interval {i+1}/{len(intervals)} ({interval.source_video})")
                continue
                
            try:
                # Get entries for this interval from the same source video
                start_seconds = self.parse_timestamp(interval.start_time)
                end_seconds = self.parse_timestamp(interval.end_time)
                
                interval_entries = [
                    e for e in entries 
                    if (e.source_video == interval.source_video and 
                        start_seconds <= self.parse_timestamp(e.timestamp) <= end_seconds)
                ]
                
                # Create a brief content summary for AI context
                transcript_parts = []
                visual_parts = []
                
                for entry in interval_entries[:10]:  # Limit to first 10 entries
                    if entry.entry_type == 'transcript' and entry.content:
                        speaker_prefix = f"{entry.speaker}: " if entry.speaker else ""
                        transcript_parts.append(f"{speaker_prefix}{entry.content}")
                    elif entry.entry_type == 'keyframe':
                        visual_parts.append(entry.content[:100])
                
                transcript_text = " | ".join(transcript_parts[:5])
                visual_text = " | ".join(visual_parts[:2])
                
                prompt = f"""
Based on this narrative context:
"{narrative[:1000]}..."

This video segment from {interval.source_video} ({interval.start_time} to {interval.end_time}) contains:
Dialogue/Audio: {transcript_text}
Visuals: {visual_text}

Generate a concise, engaging description (15-25 words) of what's happening in this segment. Focus on the main action, emotion, or story beat. Make it punchy and descriptive for video editing.
"""
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a video editor creating brief, punchy descriptions for video segments. Keep it concise and engaging."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=80,
                    temperature=0.7
                )
                
                ai_description = response.choices[0].message.content
                if ai_description:
                    interval.ai_description = ai_description.strip()
                else:
                    interval.ai_description = f"Video segment from {interval.source_video}"
                
                print(f"Generated description for interval {i+1}/{len(intervals)} ({interval.source_video})")
                
            except Exception as e:
                print(f"Error generating AI description for interval {i+1}: {e}")
                if not interval.ai_description:
                    interval.ai_description = f"Video segment from {interval.source_video}"
        
        return intervals
    
    def save_results(self, intervals: List[TimeInterval], output_file: str):
        """Save the intervals to a JSON file"""
        results = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "narrative_file": self.narrative_file,
                "stream_directory": self.stream_dir,
                "total_target_duration": self.total_duration,
                "suggested_interval_duration": self.suggested_interval_duration,
                "min_interval_duration": self.min_interval_duration,
                "max_interval_duration": self.max_interval_duration,
                "actual_total_duration": sum(i.duration_seconds for i in intervals),
                "total_intervals": len(intervals),
                "videos_used": list(set(i.source_video for i in intervals))
            },
            "intervals": []
        }
        
        for i, interval in enumerate(intervals):
            results["intervals"].append({
                "index": i + 1,
                "start_time": interval.start_time,
                "end_time": interval.end_time,
                "duration_seconds": round(interval.duration_seconds, 2),
                "ai_description": interval.ai_description,
                "source_video": interval.source_video
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {output_file}")
    
    def generate_intervals(self, output_file: Optional[str] = None):
        """Main method to generate intervals"""
        print("Reading narrative...")
        narrative = self.read_narrative()
        
        print("Reading stream files...")
        entries = self.read_all_stream_files()
        print(f"Found {len(entries)} total stream entries")
        
        if not entries:
            print("No stream entries found!")
            return
        
        print("Creating dynamic intervals based on story flow...")
        intervals = self.create_intervals(entries, narrative)
        print(f"Created {len(intervals)} total intervals")
        
        if not intervals:
            print("No intervals created!")
            return
        
        print("Generating AI descriptions...")
        intervals = self.generate_ai_descriptions(intervals, entries, narrative)
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"narrative_intervals_{timestamp}.json"
        
        self.save_results(intervals, output_file)
        
        # Print summary
        total_duration = sum(i.duration_seconds for i in intervals)
        video_counts = {}
        for interval in intervals:
            video_counts[interval.source_video] = video_counts.get(interval.source_video, 0) + 1
        
        print("\n" + "="*70)
        print("GENERATED INTERVALS SUMMARY")
        print("="*70)
        print(f"Total Duration: {total_duration:.1f}s (Target: {self.total_duration}s)")
        print(f"Number of Intervals: {len(intervals)}")
        print(f"Videos Used: {', '.join(video_counts.keys())}")
        for video, count in video_counts.items():
            print(f"  - {video}: {count} intervals")
        print("-"*70)
        for i, interval in enumerate(intervals):
            print(f"{i+1}. {interval.source_video} | {interval.start_time} - {interval.end_time} ({interval.duration_seconds:.1f}s)")
            print(f"   {interval.ai_description}")
            print()

def main():
    parser = argparse.ArgumentParser(description="Generate dynamic timestamp intervals from narrative and stream data")
    parser.add_argument("narrative_file", help="Path to the narrative text file")
    parser.add_argument("--stream-dir", default="stream_processed_clip", 
                       help="Directory containing processed stream files")
    parser.add_argument("--duration", type=int, default=60, 
                       help="Total target duration for entire video in seconds (default: 60s/1min)")
    parser.add_argument("--interval-duration", type=int, default=5,
                       help="Suggested duration for each individual interval in seconds (default: 5s)")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    
    args = parser.parse_args()
    
    try:
        generator = NarrativeIntervalGenerator(
            narrative_file=args.narrative_file,
            stream_dir=args.stream_dir,
            total_duration=args.duration,
            suggested_interval_duration=args.interval_duration
        )
        
        generator.generate_intervals(args.output)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 