"""
Main NLP processor that orchestrates the entire narrative generation pipeline
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from .data_preprocessor import DataPreprocessor, VideoEntry, TimeSegment
from .style_adapter import StyleAdapter
from .narrative_generator import NarrativeGenerator, NarrativeSegment
from .output_formatter import OutputFormatter
from .config import processing_config, ERROR_MESSAGES

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of NLP processing"""
    success: bool
    narrative_segments: List[NarrativeSegment]
    metadata: Dict[str, Any]
    error_message: Optional[str] = None

class NLPProcessor:
    """Main processor that orchestrates the entire NLP pipeline"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.data_preprocessor = DataPreprocessor(processing_config.time_window_seconds)
        self.style_adapter = StyleAdapter()
        self.narrative_generator = NarrativeGenerator(api_key)
        self.output_formatter = OutputFormatter()
        
        # Validate API key
        if not self.narrative_generator.client.api_key:
            raise ValueError("OpenAI API key is required for NLP processing")
    
    def process_videos(self, 
                      video_outputs: List[str], 
                      style: str = "inspiring",
                      user_prompt: Optional[str] = None,
                      title: str = "Generated Narrative") -> ProcessingResult:
        """
        Process multiple video outputs to generate narrative
        
        Args:
            video_outputs: List of paths to processed video files
            style: Target narrative style
            user_prompt: Optional user-provided prompt
            title: Narrative title
            
        Returns:
            ProcessingResult with narrative segments and metadata
        """
        try:
            logger.info(f"Starting NLP processing for {len(video_outputs)} videos")
            
            # Step 1: Parse and preprocess video data
            logger.info("Step 1: Parsing and preprocessing video data")
            entries = self._parse_video_data(video_outputs)
            
            # Step 2: Validate input data
            logger.info("Step 2: Validating input data")
            self._validate_input_data(entries)
            
            # Step 3: Parse and validate style
            logger.info("Step 3: Processing style preferences")
            validated_style = self._process_style(style)
            
            # Step 4: Create time segments
            logger.info("Step 4: Creating time segments")
            segments = self._create_time_segments(entries)
            
            # Step 5: Generate narrative segments
            logger.info("Step 5: Generating narrative segments")
            narrative_segments = self._generate_narrative_segments(segments, validated_style, user_prompt)
            
            # Step 6: Ensure narrative coherence
            logger.info("Step 6: Ensuring narrative coherence")
            coherent_segments = self._ensure_coherence(narrative_segments)
            
            # Step 7: Create metadata
            logger.info("Step 7: Creating processing metadata")
            metadata = self._create_metadata(entries, coherent_segments, validated_style, user_prompt, title)
            
            logger.info(f"NLP processing completed successfully. Generated {len(coherent_segments)} narrative segments")
            
            return ProcessingResult(
                success=True,
                narrative_segments=coherent_segments,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"NLP processing failed: {e}")
            return ProcessingResult(
                success=False,
                narrative_segments=[],
                metadata={},
                error_message=str(e)
            )
    
    def run_nlp_pipeline(self, 
                        input_data: Dict[str, Any], 
                        config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete NLP pipeline with configuration
        
        Args:
            input_data: Input data dictionary
            config: Configuration dictionary
            
        Returns:
            Complete output dictionary
        """
        try:
            # Extract parameters from input_data and config
            video_outputs = input_data.get('video_outputs', [])
            style = config.get('style', 'inspiring')
            user_prompt = config.get('user_prompt')
            title = config.get('title', 'Generated Narrative')
            
            # Process videos
            result = self.process_videos(video_outputs, style, user_prompt, title)
            
            if not result.success:
                return {
                    'success': False,
                    'error': result.error_message,
                    'metadata': result.metadata
                }
            
            # Generate outputs
            outputs = {}
            
            # JSON output for video pipeline
            json_output = self.output_formatter.generate_json_script(
                result.narrative_segments, title, style, user_prompt
            )
            outputs['json'] = json_output
            
            # Markdown output for human review
            markdown_output = self.output_formatter.generate_markdown_script(
                result.narrative_segments, title, style, user_prompt
            )
            outputs['markdown'] = markdown_output
            
            # Video script format
            script_output = self.output_formatter.create_video_script_format(
                result.narrative_segments
            )
            outputs['script'] = script_output
            
            return {
                'success': True,
                'outputs': outputs,
                'metadata': result.metadata,
                'segments_count': len(result.narrative_segments)
            }
            
        except Exception as e:
            logger.error(f"NLP pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {}
            }
    
    def handle_processing_errors(self, error: Exception) -> Dict[str, Any]:
        """
        Handle processing errors gracefully
        
        Args:
            error: Exception that occurred
            
        Returns:
            Error information dictionary
        """
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': str(logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))),
            'suggestions': []
        }
        
        # Provide specific suggestions based on error type
        if "API key" in str(error):
            error_info['suggestions'].append("Check that OPENAI_API_KEY environment variable is set")
            error_info['suggestions'].append("Verify the API key is valid and has sufficient credits")
        
        elif "video data" in str(error):
            error_info['suggestions'].append("Ensure video output files exist and are readable")
            error_info['suggestions'].append("Check that files contain valid EZCut output format")
        
        elif "style" in str(error):
            error_info['suggestions'].append("Use one of the available styles: inspiring, corporate, funny, etc.")
            error_info['suggestions'].append("Check spelling and case sensitivity")
        
        elif "API" in str(error):
            error_info['suggestions'].append("Check internet connection")
            error_info['suggestions'].append("Verify OpenAI API service is available")
            error_info['suggestions'].append("Consider reducing content length or chunking")
        
        return error_info
    
    def validate_input_data(self, data: List[VideoEntry]) -> bool:
        """
        Validate input data for processing
        
        Args:
            data: List of video entries
            
        Returns:
            True if valid, raises ValueError if not
        """
        return self.data_preprocessor.validate_input_data(data)
    
    def _parse_video_data(self, video_outputs: List[str]) -> List[VideoEntry]:
        """Parse video output files"""
        if not video_outputs:
            raise ValueError("No video output files provided")
        
        # Check if files exist
        for output_file in video_outputs:
            if not Path(output_file).exists():
                raise ValueError(f"Video output file not found: {output_file}")
        
        # Parse and merge all video outputs
        entries = self.data_preprocessor.merge_multiple_videos(video_outputs)
        
        if not entries:
            raise ValueError(ERROR_MESSAGES["no_video_data"])
        
        return entries
    
    def _validate_input_data(self, entries: List[VideoEntry]) -> None:
        """Validate input data"""
        try:
            self.data_preprocessor.validate_input_data(entries)
        except ValueError as e:
            raise ValueError(f"Input validation failed: {e}")
    
    def _process_style(self, style: str) -> str:
        """Process and validate style preference"""
        try:
            return self.style_adapter.parse_style_preference(style)
        except ValueError as e:
            raise ValueError(f"Style processing failed: {e}")
    
    def _create_time_segments(self, entries: List[VideoEntry]) -> List[TimeSegment]:
        """Create time segments from video entries"""
        segments = self.data_preprocessor.create_time_segments(entries)
        
        if not segments:
            raise ValueError("No valid time segments created from video data")
        
        return segments
    
    def _generate_narrative_segments(self, 
                                   segments: List[TimeSegment], 
                                   style: str, 
                                   user_prompt: Optional[str]) -> List[NarrativeSegment]:
        """Generate narrative segments for all time segments"""
        narrative_segments = []
        
        for segment in segments:
            try:
                narrative_segment = self.narrative_generator.generate_narrative_segment(
                    transcripts=segment.transcripts,
                    keyframes=segment.keyframes,
                    style=style,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    user_prompt=user_prompt
                )
                narrative_segments.append(narrative_segment)
                
            except Exception as e:
                logger.warning(f"Failed to generate narrative for segment {segment.start_time}-{segment.end_time}: {e}")
                # Continue with other segments
                continue
        
        if not narrative_segments:
            raise ValueError("No narrative segments were successfully generated")
        
        return narrative_segments
    
    def _ensure_coherence(self, segments: List[NarrativeSegment]) -> List[NarrativeSegment]:
        """Ensure narrative coherence across segments"""
        try:
            return self.narrative_generator.maintain_narrative_coherence(segments)
        except Exception as e:
            logger.warning(f"Coherence improvement failed: {e}")
            return segments  # Return original segments if coherence fails
    
    def _create_metadata(self, 
                        entries: List[VideoEntry], 
                        segments: List[NarrativeSegment], 
                        style: str, 
                        user_prompt: Optional[str],
                        title: str) -> Dict[str, Any]:
        """Create comprehensive processing metadata"""
        # Get content summary
        content_summary = self.data_preprocessor.get_content_summary(entries)
        
        # Calculate narrative statistics
        total_duration = max(segment.end_time for segment in segments) if segments else 0
        avg_confidence = sum(segment.confidence for segment in segments) / len(segments) if segments else 0
        
        metadata = {
            'processing_info': {
                'title': title,
                'style': style,
                'user_prompt': user_prompt,
                'total_segments': len(segments),
                'total_duration_seconds': total_duration,
                'total_duration_formatted': self._format_timestamp(total_duration),
                'average_confidence': round(avg_confidence, 3),
                'processing_timestamp': str(logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None)))
            },
            'content_summary': content_summary,
            'style_info': {
                'applied_style': style,
                'style_template': self.style_adapter.get_style_template(style).__dict__
            },
            'quality_metrics': {
                'high_confidence_segments': sum(1 for s in segments if s.confidence >= 0.7),
                'medium_confidence_segments': sum(1 for s in segments if 0.4 <= s.confidence < 0.7),
                'low_confidence_segments': sum(1 for s in segments if s.confidence < 0.4),
                'fallback_segments': sum(1 for s in segments if s.metadata.get('fallback', False))
            }
        }
        
        return metadata
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def export_results(self, 
                      result: ProcessingResult, 
                      output_dir: str, 
                      title: str = "narrative") -> Dict[str, str]:
        """
        Export processing results to files
        
        Args:
            result: Processing result
            output_dir: Output directory
            title: Base title for files
            
        Returns:
            Dictionary of exported file paths
        """
        if not result.success:
            raise ValueError("Cannot export failed processing result")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        # Export JSON
        json_output = self.output_formatter.generate_json_script(
            result.narrative_segments, title, result.metadata['processing_info']['style']
        )
        json_path = Path(output_dir) / f"{title}.json"
        if self.output_formatter.export_to_file(json_output, str(json_path), "json"):
            exported_files['json'] = str(json_path)
        
        # Export Markdown
        markdown_output = self.output_formatter.generate_markdown_script(
            result.narrative_segments, title, result.metadata['processing_info']['style']
        )
        md_path = Path(output_dir) / f"{title}.md"
        if self.output_formatter.export_to_file(markdown_output, str(md_path), "markdown"):
            exported_files['markdown'] = str(md_path)
        
        # Export Script
        script_output = self.output_formatter.create_video_script_format(
            result.narrative_segments
        )
        script_path = Path(output_dir) / f"{title}_script.txt"
        if self.output_formatter.export_to_file(script_output, str(script_path), "script"):
            exported_files['script'] = str(script_path)
        
        return exported_files 