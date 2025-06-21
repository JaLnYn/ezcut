#!/usr/bin/env python3
"""
Main entry point for the NLP pipeline
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from nlp.nlp_processor import NLPProcessor
from nlp.config import style_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function for NLP pipeline"""
    parser = argparse.ArgumentParser(
        description="NLP Pipeline for Video Narrative Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all videos in outputs/ directory with inspiring style
  python main_nlp.py --input-dir outputs/ --style inspiring

  # Process specific files with custom prompt
  python main_nlp.py --files outputs/video1.txt outputs/video2.txt --style corporate --prompt "Focus on business outcomes"

  # Process with funny style and custom title
  python main_nlp.py --input-dir outputs/ --style funny --title "Hilarious Hackathon Highlights"

  # Export to specific directory
  python main_nlp.py --input-dir outputs/ --output-dir narratives/ --style energetic
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--input-dir', '-i',
        type=str,
        help='Directory containing processed video files'
    )
    input_group.add_argument(
        '--files', '-f',
        nargs='+',
        type=str,
        help='Specific video output files to process'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='nlp_outputs',
        help='Output directory for generated narratives (default: nlp_outputs)'
    )
    
    # Style and content options
    parser.add_argument(
        '--style', '-s',
        type=str,
        default='inspiring',
        choices=style_config.available_styles,
        help=f'Narrative style (default: inspiring). Available: {", ".join(style_config.available_styles)}'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        type=str,
        help='Custom user prompt for narrative generation'
    )
    
    parser.add_argument(
        '--title', '-t',
        type=str,
        default='Generated Narrative',
        help='Title for the generated narrative (default: Generated Narrative)'
    )
    
    # Configuration options
    parser.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key (or set OPENAI_API_KEY environment variable)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without actually running'
    )
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Get video output files
        video_outputs = get_video_outputs(args)
        
        if not video_outputs:
            logger.error("No video output files found!")
            return 1
        
        if args.dry_run:
            print_dry_run_info(video_outputs, args)
            return 0
        
        # Initialize NLP processor
        logger.info("Initializing NLP processor...")
        processor = NLPProcessor(api_key=args.api_key)
        
        # Process videos
        logger.info(f"Processing {len(video_outputs)} video outputs...")
        result = processor.process_videos(
            video_outputs=video_outputs,
            style=args.style,
            user_prompt=args.prompt,
            title=args.title
        )
        
        if not result.success:
            logger.error(f"NLP processing failed: {result.error_message}")
            return 1
        
        # Export results
        logger.info("Exporting results...")
        exported_files = processor.export_results(
            result=result,
            output_dir=args.output_dir,
            title=args.title.lower().replace(' ', '_')
        )
        
        # Print success summary
        print_success_summary(result, exported_files, args)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

def get_video_outputs(args) -> List[str]:
    """Get list of video output files to process"""
    video_outputs = []
    
    if args.input_dir:
        # Process all files in directory
        input_path = Path(args.input_dir)
        if not input_path.exists():
            logger.error(f"Input directory not found: {args.input_dir}")
            return []
        
        # Find all processed video files
        for file_path in input_path.glob("*_processed.txt"):
            if file_path.is_file():
                video_outputs.append(str(file_path))
        
        if not video_outputs:
            logger.warning(f"No processed video files found in {args.input_dir}")
            # Try alternative patterns
            for file_path in input_path.glob("*.txt"):
                if file_path.is_file() and "processed" in file_path.name:
                    video_outputs.append(str(file_path))
    
    elif args.files:
        # Process specific files
        for file_path in args.files:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
            video_outputs.append(str(path))
    
    return sorted(video_outputs)

def print_dry_run_info(video_outputs: List[str], args):
    """Print dry run information"""
    print("=== DRY RUN - NLP Pipeline ===")
    print(f"Input files ({len(video_outputs)}):")
    for file_path in video_outputs:
        print(f"  - {file_path}")
    
    print(f"\nConfiguration:")
    print(f"  Style: {args.style}")
    print(f"  Title: {args.title}")
    if args.prompt:
        print(f"  Prompt: {args.prompt}")
    print(f"  Output directory: {args.output_dir}")
    
    print(f"\nAvailable styles: {', '.join(style_config.available_styles)}")
    print("\nRun without --dry-run to execute the pipeline.")

def print_success_summary(result, exported_files: Dict[str, str], args):
    """Print success summary"""
    print("\n" + "="*50)
    print("✅ NLP PROCESSING COMPLETED SUCCESSFULLY")
    print("="*50)
    
    # Processing summary
    metadata = result.metadata
    processing_info = metadata['processing_info']
    
    print(f"\n📊 Processing Summary:")
    print(f"  Title: {processing_info['title']}")
    print(f"  Style: {processing_info['style']}")
    print(f"  Total segments: {processing_info['total_segments']}")
    print(f"  Duration: {processing_info['total_duration_formatted']}")
    print(f"  Average confidence: {processing_info['average_confidence']:.2f}")
    
    # Quality metrics
    quality_metrics = metadata['quality_metrics']
    print(f"\n🎯 Quality Metrics:")
    print(f"  High confidence (≥0.7): {quality_metrics['high_confidence_segments']}")
    print(f"  Medium confidence (0.4-0.7): {quality_metrics['medium_confidence_segments']}")
    print(f"  Low confidence (<0.4): {quality_metrics['low_confidence_segments']}")
    if quality_metrics['fallback_segments'] > 0:
        print(f"  Fallback segments: {quality_metrics['fallback_segments']}")
    
    # Content summary
    content_summary = metadata['content_summary']
    print(f"\n📹 Content Summary:")
    print(f"  Sources: {len(content_summary['sources'])}")
    print(f"  Transcripts: {content_summary['transcript_count']}")
    print(f"  Keyframes: {content_summary['keyframe_count']}")
    
    # Exported files
    print(f"\n📁 Exported Files:")
    for file_type, file_path in exported_files.items():
        print(f"  {file_type.upper()}: {file_path}")
    
    print(f"\n🚀 Next Steps:")
    print(f"  - Review the markdown file for narrative quality")
    print(f"  - Use the JSON file for video rendering pipeline")
    print(f"  - Use the script file for voice-over generation")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    exit(main()) 