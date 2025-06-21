"""
Style adaptation module for handling different narrative tones and styles
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
import re

from .config import STYLE_TEMPLATES, style_config, ERROR_MESSAGES

logger = logging.getLogger(__name__)

@dataclass
class StyleContext:
    """Context information for style adaptation"""
    style: str
    tone: str
    vocabulary: List[str]
    structure: str
    prompt_suffix: str
    intensity: float  # 0.0 to 1.0 for style intensity

class StyleAdapter:
    """Handles style and tone adaptation for narrative generation"""
    
    def __init__(self):
        self.available_styles = style_config.available_styles
        self.default_style = style_config.default_style
    
    def parse_style_preference(self, style_input: str) -> str:
        """
        Parse and validate user style preference
        
        Args:
            style_input: User-provided style string
            
        Returns:
            Validated style string
        """
        if not style_input:
            return self.default_style
        
        # Normalize input
        style = style_input.lower().strip()
        
        # Handle variations and synonyms
        style_mapping = {
            'inspirational': 'inspiring',
            'motivational': 'inspiring',
            'business': 'corporate',
            'formal': 'corporate',
            'humorous': 'funny',
            'comedy': 'funny',
            'relaxed': 'casual',
            'informal': 'casual',
            'technical': 'professional',
            'academic': 'professional',
            'dynamic': 'energetic',
            'high-energy': 'energetic',
            'peaceful': 'calm',
            'serene': 'calm',
            'intense': 'dramatic',
            'emotional': 'dramatic'
        }
        
        # Map to standard style
        if style in style_mapping:
            style = style_mapping[style]
        
        # Validate style
        if style not in self.available_styles:
            available_str = ', '.join(self.available_styles)
            raise ValueError(ERROR_MESSAGES["invalid_style"].format(
                style=style_input, available_styles=available_str
            ))
        
        logger.info(f"Using style: {style}")
        return style
    
    def get_style_template(self, style: str) -> StyleContext:
        """
        Get style template and context
        
        Args:
            style: Validated style string
            
        Returns:
            StyleContext object with style information
        """
        if style not in STYLE_TEMPLATES:
            raise ValueError(f"Style template not found: {style}")
        
        template = STYLE_TEMPLATES[style]
        
        return StyleContext(
            style=style,
            tone=template["tone"],
            vocabulary=template["vocabulary"].split(", "),
            structure=template["structure"],
            prompt_suffix=template["prompt_suffix"],
            intensity=0.8  # Default intensity
        )
    
    def adapt_narrative_tone(self, content: str, style: str, intensity: float = 0.8) -> str:
        """
        Adapt existing content to match the specified style
        
        Args:
            content: Original content
            style: Target style
            intensity: Style intensity (0.0 to 1.0)
            
        Returns:
            Style-adapted content
        """
        style_context = self.get_style_template(style)
        style_context.intensity = max(0.0, min(1.0, intensity))
        
        adapted_content = content
        
        # Apply vocabulary adaptation
        adapted_content = self._adapt_vocabulary(adapted_content, style_context)
        
        # Apply tone adaptation
        adapted_content = self._adapt_tone(adapted_content, style_context)
        
        # Apply structure adaptation
        adapted_content = self._adapt_structure(adapted_content, style_context)
        
        return adapted_content
    
    def _adapt_vocabulary(self, content: str, style_context: StyleContext) -> str:
        """Adapt vocabulary to match style"""
        adapted = content
        
        # Style-specific vocabulary enhancements
        if style_context.style == "inspiring":
            inspiring_words = ["breakthrough", "innovation", "passion", "vision", "transform", "empower", "unleash"]
            adapted = self._enhance_with_vocabulary(adapted, inspiring_words, style_context.intensity)
        
        elif style_context.style == "corporate":
            corporate_words = ["strategy", "execution", "results", "leadership", "excellence", "optimize", "leverage"]
            adapted = self._enhance_with_vocabulary(adapted, corporate_words, style_context.intensity)
        
        elif style_context.style == "funny":
            funny_words = ["hilarious", "unexpected", "clever", "witty", "amusing", "brilliant", "genius"]
            adapted = self._enhance_with_vocabulary(adapted, funny_words, style_context.intensity)
        
        elif style_context.style == "energetic":
            energetic_words = ["explosive", "dynamic", "powerful", "intense", "electrifying", "thrilling", "amazing"]
            adapted = self._enhance_with_vocabulary(adapted, energetic_words, style_context.intensity)
        
        return adapted
    
    def _enhance_with_vocabulary(self, content: str, vocabulary: List[str], intensity: float) -> str:
        """Enhance content with style-specific vocabulary"""
        if intensity < 0.3:
            return content  # Low intensity, minimal changes
        
        # Simple vocabulary enhancement (more sophisticated version could use NLP)
        enhanced = content
        
        # Add style words at appropriate positions
        if intensity > 0.7:
            # High intensity - add more style words
            for word in vocabulary[:3]:  # Use first 3 words
                if word not in enhanced.lower():
                    # Add at the beginning or end
                    if not enhanced.endswith('.'):
                        enhanced += f". This is truly {word}."
                    else:
                        enhanced += f" It's absolutely {word}."
        
        return enhanced
    
    def _adapt_tone(self, content: str, style_context: StyleContext) -> str:
        """Adapt the tone of the content"""
        adapted = content
        
        if style_context.style == "inspiring":
            # Make more motivational
            adapted = self._make_inspiring(adapted, style_context.intensity)
        
        elif style_context.style == "corporate":
            # Make more professional
            adapted = self._make_corporate(adapted, style_context.intensity)
        
        elif style_context.style == "funny":
            # Add humor elements
            adapted = self._make_funny(adapted, style_context.intensity)
        
        elif style_context.style == "casual":
            # Make more conversational
            adapted = self._make_casual(adapted, style_context.intensity)
        
        return adapted
    
    def _make_inspiring(self, content: str, intensity: float) -> str:
        """Make content more inspiring"""
        if intensity < 0.5:
            return content
        
        # Add inspiring elements
        inspiring_phrases = [
            "This is truly remarkable",
            "What an incredible moment",
            "The possibilities are endless",
            "This is just the beginning",
            "The future is bright"
        ]
        
        if intensity > 0.7 and not any(phrase.lower() in content.lower() for phrase in inspiring_phrases):
            content = f"{inspiring_phrases[0]}. {content}"
        
        return content
    
    def _make_corporate(self, content: str, intensity: float) -> str:
        """Make content more corporate/professional"""
        if intensity < 0.5:
            return content
        
        # Replace casual language with professional terms
        replacements = {
            "guys": "team members",
            "awesome": "excellent",
            "cool": "impressive",
            "amazing": "remarkable",
            "great": "outstanding"
        }
        
        for casual, professional in replacements.items():
            content = re.sub(rf'\b{casual}\b', professional, content, flags=re.IGNORECASE)
        
        return content
    
    def _make_funny(self, content: str, intensity: float) -> str:
        """Add humor to content"""
        if intensity < 0.5:
            return content
        
        # Simple humor additions (more sophisticated version could use comedy patterns)
        funny_additions = [
            " (and yes, it's as awesome as it sounds)",
            " - because why not?",
            " (plot twist: it actually worked!)",
            " - the kind of moment that makes you question reality"
        ]
        
        if intensity > 0.7 and not content.endswith(')'):
            import random
            content += random.choice(funny_additions)
        
        return content
    
    def _make_casual(self, content: str, intensity: float) -> str:
        """Make content more casual/conversational"""
        if intensity < 0.5:
            return content
        
        # Replace formal language with casual equivalents
        replacements = {
            "individuals": "people",
            "participants": "folks",
            "demonstrated": "showed",
            "utilized": "used",
            "implemented": "made"
        }
        
        for formal, casual in replacements.items():
            content = re.sub(rf'\b{formal}\b', casual, content, flags=re.IGNORECASE)
        
        return content
    
    def _adapt_structure(self, content: str, style_context: StyleContext) -> str:
        """Adapt content structure to match style"""
        # This is a simplified version - more sophisticated structure adaptation
        # would involve sentence-level analysis and restructuring
        
        if style_context.style == "energetic" and style_context.intensity > 0.7:
            # Add exclamation marks for energy
            if not content.endswith('!'):
                content += '!'
        
        elif style_context.style == "calm" and style_context.intensity > 0.7:
            # Make sentences longer and more flowing
            sentences = content.split('. ')
            if len(sentences) > 1:
                # Combine short sentences for calm tone
                content = '. '.join(sentences[:2]) + '.'
        
        return content
    
    def create_style_prompt(self, style: str, content_type: str = "narrative") -> str:
        """
        Create a style-specific prompt for LLM generation
        
        Args:
            style: Target style
            content_type: Type of content to generate
            
        Returns:
            Formatted prompt string
        """
        style_context = self.get_style_template(style)
        
        base_prompt = f"""Generate a {content_type} in a {style_context.tone} style.

Style characteristics:
- Tone: {style_context.tone}
- Structure: {style_context.structure}
- Vocabulary focus: {', '.join(style_context.vocabulary[:5])}

{style_context.prompt_suffix}

The narrative should be engaging, coherent, and maintain the specified style throughout."""
        
        return base_prompt
    
    def validate_style_parameters(self, style: str, intensity: float = 0.8) -> bool:
        """
        Validate style parameters
        
        Args:
            style: Style string
            intensity: Intensity value
            
        Returns:
            True if valid, raises ValueError if not
        """
        # Validate style
        if style not in self.available_styles:
            available_str = ', '.join(self.available_styles)
            raise ValueError(ERROR_MESSAGES["invalid_style"].format(
                style=style, available_styles=available_str
            ))
        
        # Validate intensity
        if not 0.0 <= intensity <= 1.0:
            raise ValueError(f"Intensity must be between 0.0 and 1.0, got: {intensity}")
        
        return True
    
    def get_style_combinations(self) -> List[Dict[str, Any]]:
        """
        Get available style combinations for complex narratives
        
        Returns:
            List of style combination options
        """
        combinations = [
            {
                "name": "Dynamic Corporate",
                "primary": "corporate",
                "secondary": "energetic",
                "description": "Professional yet engaging"
            },
            {
                "name": "Inspiring Casual",
                "primary": "inspiring",
                "secondary": "casual",
                "description": "Motivational but approachable"
            },
            {
                "name": "Funny Professional",
                "primary": "funny",
                "secondary": "professional",
                "description": "Entertaining yet informative"
            },
            {
                "name": "Dramatic Calm",
                "primary": "dramatic",
                "secondary": "calm",
                "description": "Intense but controlled"
            }
        ]
        
        return combinations 