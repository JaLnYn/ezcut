"""
NLP Pipeline for Video Narrative Generation

This package provides a complete Natural Language Processing pipeline that:
- Parses EZCut video output (transcripts + keyframes)
- Generates coherent narratives using LLM
- Adapts tone and style based on user preferences
- Outputs structured formats for video rendering

Main components:
- DataPreprocessor: Parses and structures video data
- StyleAdapter: Handles narrative tone and style adaptation
- NarrativeGenerator: LLM-based story generation
- OutputFormatter: Creates structured outputs (JSON, Markdown, Script)
- NLPProcessor: Main orchestrator for the entire pipeline
"""

from .nlp_processor import NLPProcessor, ProcessingResult
from .data_preprocessor import DataPreprocessor, VideoEntry, TimeSegment
from .style_adapter import StyleAdapter, StyleContext
from .narrative_generator import NarrativeGenerator, NarrativeSegment
from .output_formatter import OutputFormatter, NarrativeOutput
from .config import llm_config, processing_config, style_config, STYLE_TEMPLATES

__version__ = "1.0.0"
__author__ = "EZCut NLP Team"

__all__ = [
    # Main processor
    "NLPProcessor",
    "ProcessingResult",
    
    # Data processing
    "DataPreprocessor", 
    "VideoEntry",
    "TimeSegment",
    
    # Style and narrative
    "StyleAdapter",
    "StyleContext",
    "NarrativeGenerator",
    "NarrativeSegment",
    
    # Output formatting
    "OutputFormatter",
    "NarrativeOutput",
    
    # Configuration
    "llm_config",
    "processing_config", 
    "style_config",
    "STYLE_TEMPLATES"
] 