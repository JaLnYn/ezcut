"""
Output formatter module for generating structured narrative outputs
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .narrative_generator import NarrativeSegment
from .config import OUTPUT_FORMATS, ERROR_MESSAGES

logger = logging.getLogger(__name__)

@dataclass
class NarrativeOutput:
    """Complete narrative output structure"""
    title: str
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timing: Dict[str, Any]
    style: str
    generated_at: str

class OutputFormatter:
    """Handles formatting of narrative output for different use cases"""
    
    def __init__(self):
        self.output_formats = OUTPUT_FORMATS
    
    def generate_json_script(self, 
                           narrative_segments: List[NarrativeSegment],
                           title: str = "Generated Narrative",
                           style: str = "inspiring",
                           user_prompt: Optional[str] = None) -> str:
        """
        Generate structured JSON output for video rendering pipeline
        
        Args:
            narrative_segments: List of narrative segments
            title: Narrative title
            style: Narrative style
            user_prompt: Original user prompt
            
        Returns:
            JSON string for video pipeline
        """
        try:
            # Create sections from narrative segments
            sections = []
            total_duration = 0
            
            for segment in narrative_segments:
                section = {
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "duration": segment.end_time - segment.start_time,
                    "narrative_text": segment.narrative_text,
                    "style": segment.style,
                    "confidence": segment.confidence,
                    "metadata": segment.metadata
                }
                sections.append(section)
                total_duration = max(total_duration, segment.end_time)
            
            # Create metadata
            metadata = {
                "title": title,
                "style": style,
                "user_prompt": user_prompt,
                "total_sections": len(sections),
                "total_duration_seconds": total_duration,
                "total_duration_formatted": self._seconds_to_timestamp(total_duration),
                "average_confidence": sum(s["confidence"] for s in sections) / len(sections) if sections else 0,
                "generated_at": datetime.now().isoformat()
            }
            
            # Create timing information
            timing = {
                "total_duration": total_duration,
                "segment_count": len(sections),
                "average_segment_duration": total_duration / len(sections) if sections else 0,
                "timeline": [
                    {
                        "time": section["start_time"],
                        "action": "start_narrative",
                        "section_index": i
                    }
                    for i, section in enumerate(sections)
                ]
            }
            
            # Create complete output structure
            output = NarrativeOutput(
                title=title,
                sections=sections,
                metadata=metadata,
                timing=timing,
                style=style,
                generated_at=datetime.now().isoformat()
            )
            
            # Convert to JSON
            json_output = json.dumps(asdict(output), indent=2, ensure_ascii=False)
            
            logger.info(f"Generated JSON output with {len(sections)} sections")
            return json_output
            
        except Exception as e:
            logger.error(f"Error generating JSON output: {e}")
            raise ValueError(ERROR_MESSAGES["validation_error"].format(error=str(e)))
    
    def generate_markdown_script(self, 
                               narrative_segments: List[NarrativeSegment],
                               title: str = "Generated Narrative",
                               style: str = "inspiring",
                               user_prompt: Optional[str] = None) -> str:
        """
        Generate human-readable markdown output
        
        Args:
            narrative_segments: List of narrative segments
            title: Narrative title
            style: Narrative style
            user_prompt: Original user prompt
            
        Returns:
            Markdown string for human review
        """
        try:
            markdown_parts = []
            
            # Header
            markdown_parts.append(f"# {title}")
            markdown_parts.append("")
            
            # Metadata
            markdown_parts.append("## Metadata")
            markdown_parts.append(f"- **Style:** {style}")
            markdown_parts.append(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            markdown_parts.append(f"- **Total Duration:** {self._seconds_to_timestamp(max(s.end_time for s in narrative_segments) if narrative_segments else 0)}")
            markdown_parts.append(f"- **Sections:** {len(narrative_segments)}")
            
            if user_prompt:
                markdown_parts.append(f"- **User Prompt:** {user_prompt}")
            
            markdown_parts.append("")
            
            # Summary
            markdown_parts.append("## Summary")
            summary = self._generate_summary(narrative_segments)
            markdown_parts.append(summary)
            markdown_parts.append("")
            
            # Sections
            markdown_parts.append("## Narrative Sections")
            markdown_parts.append("")
            
            for i, segment in enumerate(narrative_segments, 1):
                section_md = self._format_section_markdown(segment, i)
                markdown_parts.append(section_md)
                markdown_parts.append("")
            
            # Confidence analysis
            markdown_parts.append("## Quality Analysis")
            confidence_analysis = self._generate_confidence_analysis(narrative_segments)
            markdown_parts.append(confidence_analysis)
            
            return "\n".join(markdown_parts)
            
        except Exception as e:
            logger.error(f"Error generating markdown output: {e}")
            raise ValueError(ERROR_MESSAGES["validation_error"].format(error=str(e)))
    
    def validate_output_structure(self, output: Dict[str, Any]) -> bool:
        """
        Validate output structure against required format
        
        Args:
            output: Output dictionary to validate
            
        Returns:
            True if valid, raises ValueError if not
        """
        required_fields = ["sections", "metadata", "timing"]
        
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate sections
        if not isinstance(output["sections"], list):
            raise ValueError("Sections must be a list")
        
        for i, section in enumerate(output["sections"]):
            if not isinstance(section, dict):
                raise ValueError(f"Section {i} must be a dictionary")
            
            required_section_fields = ["start_time", "end_time", "narrative_text"]
            for field in required_section_fields:
                if field not in section:
                    raise ValueError(f"Section {i} missing required field: {field}")
        
        # Validate metadata
        if not isinstance(output["metadata"], dict):
            raise ValueError("Metadata must be a dictionary")
        
        # Validate timing
        if not isinstance(output["timing"], dict):
            raise ValueError("Timing must be a dictionary")
        
        return True
    
    def format_timing_for_rendering(self, timestamps: List[float]) -> List[Dict[str, Any]]:
        """
        Format timing information for video rendering
        
        Args:
            timestamps: List of timestamp values in seconds
            
        Returns:
            List of timing events for rendering
        """
        timing_events = []
        
        for i, timestamp in enumerate(timestamps):
            event = {
                "time": timestamp,
                "formatted_time": self._seconds_to_timestamp(timestamp),
                "event_type": "narrative_segment",
                "segment_index": i,
                "duration": timestamps[i+1] - timestamp if i < len(timestamps) - 1 else 0
            }
            timing_events.append(event)
        
        return timing_events
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _generate_summary(self, segments: List[NarrativeSegment]) -> str:
        """Generate a summary of the narrative"""
        if not segments:
            return "No narrative segments available."
        
        total_duration = max(segment.end_time for segment in segments)
        avg_confidence = sum(segment.confidence for segment in segments) / len(segments)
        
        summary = f"This narrative spans {self._seconds_to_timestamp(total_duration)} "
        summary += f"across {len(segments)} segments with an average confidence of {avg_confidence:.2f}. "
        
        # Add style-specific summary
        if segments:
            style = segments[0].style
            if style == "inspiring":
                summary += "The narrative maintains an inspiring and motivational tone throughout."
            elif style == "corporate":
                summary += "The narrative presents a professional and authoritative perspective."
            elif style == "funny":
                summary += "The narrative incorporates humor and entertainment elements."
            else:
                summary += f"The narrative maintains a {style} tone throughout."
        
        return summary
    
    def _format_section_markdown(self, segment: NarrativeSegment, index: int) -> str:
        """Format a single section for markdown output"""
        section_parts = []
        
        # Section header
        start_time = self._seconds_to_timestamp(segment.start_time)
        end_time = self._seconds_to_timestamp(segment.end_time)
        duration = segment.end_time - segment.start_time
        
        section_parts.append(f"### Section {index}: {start_time} - {end_time}")
        section_parts.append("")
        
        # Section metadata
        section_parts.append(f"**Duration:** {self._seconds_to_timestamp(duration)}")
        section_parts.append(f"**Style:** {segment.style}")
        section_parts.append(f"**Confidence:** {segment.confidence:.2f}")
        section_parts.append("")
        
        # Narrative text
        section_parts.append("**Narrative:**")
        section_parts.append(segment.narrative_text)
        section_parts.append("")
        
        # Additional metadata
        if segment.metadata:
            section_parts.append("**Details:**")
            for key, value in segment.metadata.items():
                if key not in ['transcript_count', 'keyframe_count', 'duration']:
                    section_parts.append(f"- {key}: {value}")
            section_parts.append("")
        
        return "\n".join(section_parts)
    
    def _generate_confidence_analysis(self, segments: List[NarrativeSegment]) -> str:
        """Generate confidence analysis for the narrative"""
        if not segments:
            return "No segments available for analysis."
        
        confidences = [segment.confidence for segment in segments]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)
        
        # Quality assessment
        if avg_confidence >= 0.8:
            quality = "Excellent"
        elif avg_confidence >= 0.6:
            quality = "Good"
        elif avg_confidence >= 0.4:
            quality = "Fair"
        else:
            quality = "Poor"
        
        analysis = f"**Overall Quality:** {quality} (Average: {avg_confidence:.2f})\n\n"
        analysis += f"- **Highest Confidence:** {max_confidence:.2f}\n"
        analysis += f"- **Lowest Confidence:** {min_confidence:.2f}\n"
        analysis += f"- **Confidence Range:** {max_confidence - min_confidence:.2f}\n\n"
        
        # Segment quality breakdown
        high_quality = sum(1 for c in confidences if c >= 0.7)
        medium_quality = sum(1 for c in confidences if 0.4 <= c < 0.7)
        low_quality = sum(1 for c in confidences if c < 0.4)
        
        analysis += "**Segment Quality Breakdown:**\n"
        analysis += f"- High Quality (≥0.7): {high_quality} segments\n"
        analysis += f"- Medium Quality (0.4-0.7): {medium_quality} segments\n"
        analysis += f"- Low Quality (<0.4): {low_quality} segments\n"
        
        return analysis
    
    def create_video_script_format(self, narrative_segments: List[NarrativeSegment]) -> str:
        """
        Create a video script format suitable for voice-over
        
        Args:
            narrative_segments: List of narrative segments
            
        Returns:
            Formatted script string
        """
        script_parts = []
        
        for i, segment in enumerate(narrative_segments, 1):
            start_time = self._seconds_to_timestamp(segment.start_time)
            script_parts.append(f"[{start_time}] {segment.narrative_text}")
        
        return "\n\n".join(script_parts)
    
    def export_to_file(self, output: str, filepath: str, format_type: str = "json") -> bool:
        """
        Export output to file
        
        Args:
            output: Output string to save
            filepath: Target file path
            format_type: Output format type
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)
            
            logger.info(f"Exported {format_type} output to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to file {filepath}: {e}")
            return False 