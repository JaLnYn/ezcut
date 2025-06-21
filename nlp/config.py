"""
Configuration settings for the NLP pipeline
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import os

@dataclass
class LLMConfig:
    """LLM configuration settings"""
    model: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.7
    max_retries: int = 3
    timeout: int = 30

@dataclass
class ProcessingConfig:
    """Processing pipeline configuration"""
    time_window_seconds: int = 60  # Group content in 60-second windows
    max_chunk_tokens: int = 4000   # Max tokens per LLM chunk
    overlap_seconds: int = 10      # Overlap between chunks
    min_segment_duration: int = 30 # Minimum segment duration in seconds

@dataclass
class StyleConfig:
    """Style and tone configuration"""
    available_styles: List[str] = None
    default_style: str = "inspiring"
    
    def __post_init__(self):
        if self.available_styles is None:
            self.available_styles = [
                "inspiring", "corporate", "funny", "casual", 
                "professional", "energetic", "calm", "dramatic"
            ]

# Style templates for different narrative tones
STYLE_TEMPLATES = {
    "inspiring": {
        "tone": "motivational and uplifting",
        "vocabulary": "breakthrough, innovation, passion, vision, transform",
        "structure": "hero's journey with clear progression",
        "prompt_suffix": "Create an inspiring narrative that motivates and uplifts the audience."
    },
    "corporate": {
        "tone": "professional and authoritative",
        "vocabulary": "strategy, execution, results, leadership, excellence",
        "structure": "logical progression with clear outcomes",
        "prompt_suffix": "Create a professional narrative suitable for business audiences."
    },
    "funny": {
        "tone": "lighthearted and entertaining",
        "vocabulary": "hilarious, unexpected, clever, witty, amusing",
        "structure": "setup and punchline with comedic timing",
        "prompt_suffix": "Create an entertaining narrative with humor and wit."
    },
    "casual": {
        "tone": "conversational and relaxed",
        "vocabulary": "cool, awesome, amazing, incredible, fantastic",
        "structure": "natural flow like a friend telling a story",
        "prompt_suffix": "Create a casual, conversational narrative."
    },
    "professional": {
        "tone": "polished and informative",
        "vocabulary": "comprehensive, detailed, thorough, systematic",
        "structure": "clear sections with logical flow",
        "prompt_suffix": "Create a professional, informative narrative."
    },
    "energetic": {
        "tone": "high-energy and dynamic",
        "vocabulary": "explosive, dynamic, powerful, intense, electrifying",
        "structure": "fast-paced with dramatic moments",
        "prompt_suffix": "Create an energetic, dynamic narrative."
    },
    "calm": {
        "tone": "peaceful and reflective",
        "vocabulary": "serene, peaceful, thoughtful, contemplative, gentle",
        "structure": "smooth transitions with reflective moments",
        "prompt_suffix": "Create a calm, reflective narrative."
    },
    "dramatic": {
        "tone": "intense and emotional",
        "vocabulary": "dramatic, intense, emotional, powerful, gripping",
        "structure": "building tension with emotional peaks",
        "prompt_suffix": "Create a dramatic, emotionally engaging narrative."
    }
}

# Default configuration instances
llm_config = LLMConfig()
processing_config = ProcessingConfig()
style_config = StyleConfig()

# Output format specifications
OUTPUT_FORMATS = {
    "json": {
        "description": "Structured JSON for video rendering pipeline",
        "required_fields": ["sections", "metadata", "timing"]
    },
    "markdown": {
        "description": "Human-readable markdown format",
        "required_fields": ["title", "sections", "summary"]
    }
}

# Validation schemas
TIMESTAMP_REGEX = r"\[(transcript|keyframe):(\d{2}:\d{2}:\d{2})\]"
VALID_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.ts'}

# Error messages
ERROR_MESSAGES = {
    "invalid_style": "Invalid style '{style}'. Available styles: {available_styles}",
    "no_video_data": "No video data found in the provided files",
    "api_error": "LLM API error: {error}",
    "parsing_error": "Error parsing video data: {error}",
    "validation_error": "Output validation failed: {error}"
} 