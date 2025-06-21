"""
Data preprocessing module for parsing and structuring EZCut output
"""

import re
import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from datetime import datetime

from .config import TIMESTAMP_REGEX, VALID_VIDEO_EXTENSIONS, ERROR_MESSAGES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VideoEntry:
    """Represents a single video entry (transcript or keyframe)"""
    entry_type: str  # 'transcript' or 'keyframe'
    timestamp: str   # HH:MM:SS format
    timestamp_seconds: float  # Converted to seconds
    content: str     # The actual content
    source_file: str # Source video file

@dataclass
class TimeSegment:
    """Represents a time segment with grouped content"""
    start_time: float
    end_time: float
    transcripts: List[str]
    keyframes: List[str]
    duration: float

class DataPreprocessor:
    """Handles parsing and preprocessing of EZCut output data"""
    
    def __init__(self, time_window_seconds: int = 60):
        self.time_window_seconds = time_window_seconds
        self.timestamp_regex = re.compile(TIMESTAMP_REGEX)
    
    def parse_ezcut_output(self, file_path: str) -> List[VideoEntry]:
        """
        Parse a single EZCut output file
        
        Args:
            file_path: Path to the processed video file
            
        Returns:
            List of VideoEntry objects
        """
        entries = []
        source_file = Path(file_path).stem
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    entry = self._parse_line(line, source_file, line_num)
                    if entry:
                        entries.append(entry)
            
            logger.info(f"Parsed {len(entries)} entries from {file_path}")
            return entries
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            raise ValueError(ERROR_MESSAGES["parsing_error"].format(error=str(e)))
    
    def _parse_line(self, line: str, source_file: str, line_num: int) -> Optional[VideoEntry]:
        """Parse a single line from EZCut output"""
        match = self.timestamp_regex.match(line)
        if not match:
            logger.warning(f"Invalid line format at line {line_num}: {line}")
            return None
        
        entry_type = match.group(1)
        timestamp = match.group(2)
        content = line[match.end():].strip()
        
        if not content:
            logger.warning(f"Empty content at line {line_num}")
            return None
        
        try:
            timestamp_seconds = self._timestamp_to_seconds(timestamp)
        except ValueError as e:
            logger.error(f"Invalid timestamp at line {line_num}: {timestamp}")
            return None
        
        return VideoEntry(
            entry_type=entry_type,
            timestamp=timestamp,
            timestamp_seconds=timestamp_seconds,
            content=content,
            source_file=source_file
        )
    
    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert HH:MM:SS timestamp to seconds"""
        try:
            hours, minutes, seconds = map(int, timestamp.split(':'))
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {timestamp}")
    
    def merge_multiple_videos(self, video_outputs: List[str]) -> List[VideoEntry]:
        """
        Merge multiple video outputs into a single timeline
        
        Args:
            video_outputs: List of paths to processed video files
            
        Returns:
            Merged and sorted list of VideoEntry objects
        """
        all_entries = []
        
        for output_file in video_outputs:
            if not Path(output_file).exists():
                logger.warning(f"File not found: {output_file}")
                continue
            
            entries = self.parse_ezcut_output(output_file)
            all_entries.extend(entries)
        
        if not all_entries:
            raise ValueError(ERROR_MESSAGES["no_video_data"])
        
        # Sort by timestamp
        all_entries.sort(key=lambda x: x.timestamp_seconds)
        
        # Remove duplicates (same timestamp and content)
        unique_entries = self._remove_duplicates(all_entries)
        
        logger.info(f"Merged {len(unique_entries)} unique entries from {len(video_outputs)} videos")
        return unique_entries
    
    def _remove_duplicates(self, entries: List[VideoEntry]) -> List[VideoEntry]:
        """Remove duplicate entries based on timestamp and content"""
        seen = set()
        unique_entries = []
        
        for entry in entries:
            key = (entry.timestamp_seconds, entry.content[:100])  # First 100 chars for comparison
            if key not in seen:
                seen.add(key)
                unique_entries.append(entry)
        
        return unique_entries
    
    def create_time_segments(self, entries: List[VideoEntry]) -> List[TimeSegment]:
        """
        Group entries into time segments for narrative processing
        
        Args:
            entries: List of VideoEntry objects
            
        Returns:
            List of TimeSegment objects
        """
        if not entries:
            return []
        
        segments = []
        current_segment = None
        
        for entry in entries:
            # Determine if we need a new segment
            if (current_segment is None or 
                entry.timestamp_seconds >= current_segment.end_time):
                
                # Save previous segment if it exists and has content
                if current_segment and (current_segment.transcripts or current_segment.keyframes):
                    segments.append(current_segment)
                
                # Create new segment
                start_time = entry.timestamp_seconds
                end_time = start_time + self.time_window_seconds
                current_segment = TimeSegment(
                    start_time=start_time,
                    end_time=end_time,
                    transcripts=[],
                    keyframes=[],
                    duration=end_time - start_time
                )
            
            # Add entry to current segment
            if entry.entry_type == 'transcript':
                current_segment.transcripts.append(entry.content)
            elif entry.entry_type == 'keyframe':
                current_segment.keyframes.append(entry.content)
        
        # Add final segment if it has content
        if current_segment and (current_segment.transcripts or current_segment.keyframes):
            segments.append(current_segment)
        
        logger.info(f"Created {len(segments)} time segments")
        return segments
    
    def clean_and_normalize_text(self, text: str) -> str:
        """
        Clean and normalize text content
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned and normalized text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common transcription artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove bracketed content
        text = re.sub(r'\(.*?\)', '', text)  # Remove parenthetical content
        
        # Normalize punctuation
        text = re.sub(r'\.{2,}', '...', text)  # Multiple dots to ellipsis
        text = re.sub(r'!{2,}', '!', text)     # Multiple exclamation marks
        text = re.sub(r'\?{2,}', '?', text)    # Multiple question marks
        
        # Remove filler words (optional)
        filler_words = {'um', 'uh', 'like', 'you know', 'sort of', 'kind of'}
        words = text.split()
        cleaned_words = [word for word in words if word.lower() not in filler_words]
        
        return ' '.join(cleaned_words)
    
    def get_content_summary(self, entries: List[VideoEntry]) -> Dict[str, Any]:
        """
        Generate a summary of the content for analysis
        
        Args:
            entries: List of VideoEntry objects
            
        Returns:
            Dictionary with content summary statistics
        """
        if not entries:
            return {}
        
        total_duration = max(entry.timestamp_seconds for entry in entries)
        transcript_count = sum(1 for entry in entries if entry.entry_type == 'transcript')
        keyframe_count = sum(1 for entry in entries if entry.entry_type == 'keyframe')
        
        # Get unique sources
        sources = list(set(entry.source_file for entry in entries))
        
        # Calculate average content length
        avg_transcript_length = 0
        avg_keyframe_length = 0
        
        if transcript_count > 0:
            transcript_lengths = [len(entry.content) for entry in entries if entry.entry_type == 'transcript']
            avg_transcript_length = sum(transcript_lengths) / len(transcript_lengths)
        
        if keyframe_count > 0:
            keyframe_lengths = [len(entry.content) for entry in entries if entry.entry_type == 'keyframe']
            avg_keyframe_length = sum(keyframe_lengths) / len(keyframe_lengths)
        
        return {
            'total_duration_seconds': total_duration,
            'total_duration_formatted': self._seconds_to_timestamp(total_duration),
            'transcript_count': transcript_count,
            'keyframe_count': keyframe_count,
            'sources': sources,
            'avg_transcript_length': round(avg_transcript_length, 2),
            'avg_keyframe_length': round(avg_keyframe_length, 2),
            'content_density': round((transcript_count + keyframe_count) / total_duration, 2) if total_duration > 0 else 0
        }
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds back to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def validate_input_data(self, entries: List[VideoEntry]) -> bool:
        """
        Validate the input data for processing
        
        Args:
            entries: List of VideoEntry objects
            
        Returns:
            True if valid, raises ValueError if not
        """
        if not entries:
            raise ValueError("No entries provided for validation")
        
        for entry in entries:
            if not entry.entry_type in ['transcript', 'keyframe']:
                raise ValueError(f"Invalid entry type: {entry.entry_type}")
            
            if entry.timestamp_seconds < 0:
                raise ValueError(f"Negative timestamp: {entry.timestamp}")
            
            if not entry.content.strip():
                raise ValueError(f"Empty content for entry at {entry.timestamp}")
        
        # Check for reasonable duration (not too long)
        max_timestamp = max(entry.timestamp_seconds for entry in entries)
        if max_timestamp > 24 * 3600:  # 24 hours
            logger.warning(f"Very long video detected: {max_timestamp} seconds")
        
        return True 