"""
Narrative generation module using LLM for story creation
"""
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from openai import OpenAI
import os

from .config import llm_config, processing_config, ERROR_MESSAGES
from .data_preprocessor import TimeSegment
from .style_adapter import StyleAdapter

logger = logging.getLogger(__name__)

@dataclass
class NarrativeSegment:
    """Represents a generated narrative segment"""
    start_time: float
    end_time: float
    narrative_text: str
    style: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class NarrativeChunk:
    """Represents a chunk of content for LLM processing"""
    content: str
    start_time: float
    end_time: float
    token_count: int
    style_context: str

class NarrativeGenerator:
    """Handles LLM-based narrative generation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.style_adapter = StyleAdapter()
        self.config = llm_config
        self.processing_config = processing_config
        
        if not self.client.api_key:
            raise ValueError("OpenAI API key is required")
    
    def generate_narrative_segment(self, 
                                 transcripts: List[str], 
                                 keyframes: List[str], 
                                 style: str,
                                 start_time: float,
                                 end_time: float,
                                 user_prompt: Optional[str] = None) -> NarrativeSegment:
        """
        Generate narrative for a single time segment
        
        Args:
            transcripts: List of transcript texts
            keyframes: List of keyframe descriptions
            style: Target narrative style
            start_time: Segment start time in seconds
            end_time: Segment end time in seconds
            user_prompt: Optional user-provided prompt
            
        Returns:
            NarrativeSegment object
        """
        try:
            # Prepare content for LLM
            content = self._prepare_content_for_llm(transcripts, keyframes)
            
            # Create style-specific prompt
            style_prompt = self.style_adapter.create_style_prompt(style, "narrative segment")
            
            # Combine with user prompt if provided
            if user_prompt:
                style_prompt += f"\n\nUser context: {user_prompt}"
            
            # Generate narrative
            narrative_text = self._call_llm(content, style_prompt, style)
            
            # Calculate confidence (simplified - could be more sophisticated)
            confidence = self._calculate_confidence(transcripts, keyframes, narrative_text)
            
            return NarrativeSegment(
                start_time=start_time,
                end_time=end_time,
                narrative_text=narrative_text,
                style=style,
                confidence=confidence,
                metadata={
                    'transcript_count': len(transcripts),
                    'keyframe_count': len(keyframes),
                    'duration': end_time - start_time,
                    'user_prompt': user_prompt
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating narrative segment: {e}")
            # Return fallback narrative
            return self._create_fallback_narrative(transcripts, keyframes, start_time, end_time, style)
    
    def chunk_content_for_llm(self, segments: List[TimeSegment], style: str) -> List[NarrativeChunk]:
        """
        Chunk content for LLM processing to handle context limits
        
        Args:
            segments: List of time segments
            style: Target style
            
        Returns:
            List of NarrativeChunk objects
        """
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_start_time = 0
        
        for segment in segments:
            # Estimate tokens for this segment
            segment_content = self._prepare_content_for_llm(segment.transcripts, segment.keyframes)
            estimated_tokens = len(segment_content.split()) * 1.3  # Rough estimation
            
            # Check if adding this segment would exceed token limit
            if current_tokens + estimated_tokens > self.processing_config.max_chunk_tokens and current_chunk:
                # Create chunk from current content
                chunk_content = self._combine_segment_content(current_chunk)
                chunks.append(NarrativeChunk(
                    content=chunk_content,
                    start_time=chunk_start_time,
                    end_time=current_chunk[-1].end_time,
                    token_count=int(current_tokens),
                    style_context=style
                ))
                
                # Start new chunk with overlap
                overlap_segments = self._get_overlap_segments(current_chunk, self.processing_config.overlap_seconds)
                current_chunk = overlap_segments
                current_tokens = sum(len(self._prepare_content_for_llm(s.transcripts, s.keyframes).split()) * 1.3 
                                   for s in overlap_segments)
                chunk_start_time = overlap_segments[0].start_time if overlap_segments else segment.start_time
            
            # Add segment to current chunk
            current_chunk.append(segment)
            current_tokens += estimated_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_content = self._combine_segment_content(current_chunk)
            chunks.append(NarrativeChunk(
                content=chunk_content,
                start_time=chunk_start_time,
                end_time=current_chunk[-1].end_time,
                token_count=int(current_tokens),
                style_context=style
            ))
        
        logger.info(f"Created {len(chunks)} chunks for LLM processing")
        return chunks
    
    def maintain_narrative_coherence(self, segments: List[NarrativeSegment]) -> List[NarrativeSegment]:
        """
        Ensure narrative coherence across segments
        
        Args:
            segments: List of narrative segments
            
        Returns:
            List of coherent narrative segments
        """
        if len(segments) <= 1:
            return segments
        
        coherent_segments = []
        
        for i, segment in enumerate(segments):
            if i == 0:
                # First segment - no changes needed
                coherent_segments.append(segment)
                continue
            
            # Check for coherence with previous segment
            coherence_score = self._calculate_coherence(segments[i-1], segment)
            
            if coherence_score < 0.5:  # Low coherence threshold
                # Regenerate segment with context from previous
                improved_segment = self._improve_coherence(segments[i-1], segment)
                coherent_segments.append(improved_segment)
            else:
                coherent_segments.append(segment)
        
        return coherent_segments
    
    def _prepare_content_for_llm(self, transcripts: List[str], keyframes: List[str]) -> str:
        """Prepare content for LLM processing"""
        content_parts = []
        
        # Add transcripts
        if transcripts:
            content_parts.append("TRANSCRIPTS:")
            for i, transcript in enumerate(transcripts, 1):
                content_parts.append(f"{i}. {transcript}")
        
        # Add keyframes
        if keyframes:
            content_parts.append("\nVISUAL CONTEXT:")
            for i, keyframe in enumerate(keyframes, 1):
                content_parts.append(f"{i}. {keyframe}")
        
        return "\n".join(content_parts)
    
    def _call_llm(self, content: str, prompt: str, style: str) -> str:
        """Make API call to LLM"""
        full_prompt = f"""{prompt}

Content to narrate:
{content}

Generate a compelling narrative segment that captures the essence of this content."""

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a skilled narrative writer who creates engaging, coherent stories from video content."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            narrative = response.choices[0].message.content.strip()
            
            if not narrative:
                raise ValueError("Empty response from LLM")
            
            return narrative
            
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise ValueError(ERROR_MESSAGES["api_error"].format(error=str(e)))
    
    def _calculate_confidence(self, transcripts: List[str], keyframes: List[str], narrative: str) -> float:
        """Calculate confidence score for generated narrative"""
        # Simple confidence calculation based on content coverage
        total_content = len(transcripts) + len(keyframes)
        if total_content == 0:
            return 0.0
        
        # Check if narrative mentions key elements from content
        content_words = set()
        for transcript in transcripts:
            content_words.update(transcript.lower().split())
        for keyframe in keyframes:
            content_words.update(keyframe.lower().split())
        
        narrative_words = set(narrative.lower().split())
        
        # Calculate overlap
        overlap = len(content_words.intersection(narrative_words))
        coverage = overlap / len(content_words) if content_words else 0
        
        # Additional factors
        length_factor = min(len(narrative.split()) / 50, 1.0)  # Prefer longer narratives
        coherence_factor = 1.0 if len(narrative.split()) > 10 else 0.5
        
        confidence = (coverage * 0.6 + length_factor * 0.2 + coherence_factor * 0.2)
        return min(confidence, 1.0)
    
    def _create_fallback_narrative(self, transcripts: List[str], keyframes: List[str], 
                                 start_time: float, end_time: float, style: str) -> NarrativeSegment:
        """Create a fallback narrative when LLM fails"""
        duration = end_time - start_time
        
        if transcripts:
            # Use first transcript as base
            base_text = transcripts[0]
            if len(transcripts) > 1:
                base_text += f" The scene continues with more dialogue and activity."
        elif keyframes:
            # Use keyframe description
            base_text = f"The scene shows {keyframes[0].lower()}"
        else:
            base_text = f"A {duration:.0f}-second segment of video content."
        
        # Apply basic style adaptation
        adapted_text = self.style_adapter.adapt_narrative_tone(base_text, style, intensity=0.5)
        
        return NarrativeSegment(
            start_time=start_time,
            end_time=end_time,
            narrative_text=adapted_text,
            style=style,
            confidence=0.3,  # Low confidence for fallback
            metadata={
                'transcript_count': len(transcripts),
                'keyframe_count': len(keyframes),
                'duration': duration,
                'fallback': True
            }
        )
    
    def _combine_segment_content(self, segments: List[TimeSegment]) -> str:
        """Combine multiple segments into single content string"""
        all_transcripts = []
        all_keyframes = []
        
        for segment in segments:
            all_transcripts.extend(segment.transcripts)
            all_keyframes.extend(segment.keyframes)
        
        return self._prepare_content_for_llm(all_transcripts, all_keyframes)
    
    def _get_overlap_segments(self, segments: List[TimeSegment], overlap_seconds: int) -> List[TimeSegment]:
        """Get segments for overlap to maintain continuity"""
        if not segments:
            return []
        
        overlap_start = segments[-1].end_time - overlap_seconds
        overlap_segments = []
        
        for segment in segments:
            if segment.end_time > overlap_start:
                overlap_segments.append(segment)
        
        return overlap_segments
    
    def _calculate_coherence(self, prev_segment: NarrativeSegment, curr_segment: NarrativeSegment) -> float:
        """Calculate coherence between two narrative segments"""
        # Simple coherence calculation based on word overlap
        prev_words = set(prev_segment.narrative_text.lower().split())
        curr_words = set(curr_segment.narrative_text.lower().split())
        
        if not prev_words or not curr_words:
            return 0.0
        
        overlap = len(prev_words.intersection(curr_words))
        total_unique = len(prev_words.union(curr_words))
        
        return overlap / total_unique if total_unique > 0 else 0.0
    
    def _improve_coherence(self, prev_segment: NarrativeSegment, curr_segment: NarrativeSegment) -> NarrativeSegment:
        """Improve coherence by regenerating with context"""
        context_prompt = f"""Previous narrative segment: "{prev_segment.narrative_text}"

Generate a coherent continuation that flows naturally from the previous segment while maintaining the same style and tone."""

        try:
            improved_narrative = self._call_llm(
                curr_segment.metadata.get('content', ''),
                context_prompt,
                curr_segment.style
            )
            
            return NarrativeSegment(
                start_time=curr_segment.start_time,
                end_time=curr_segment.end_time,
                narrative_text=improved_narrative,
                style=curr_segment.style,
                confidence=curr_segment.confidence * 0.9,  # Slightly lower confidence for regeneration
                metadata=curr_segment.metadata
            )
            
        except Exception as e:
            logger.warning(f"Failed to improve coherence: {e}")
            return curr_segment  # Return original if improvement fails
    
    def handle_llm_api_calls(self, prompt: str, style: str, retries: int = None) -> str:
        """Handle LLM API calls with retry logic"""
        max_retries = retries or self.config.max_retries
        
        for attempt in range(max_retries):
            try:
                return self._call_llm("", prompt, style)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                logger.warning(f"LLM API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("All LLM API call attempts failed") 