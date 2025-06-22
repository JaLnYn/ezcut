#!/usr/bin/env python3
"""
Demo script showing how to use the narrative interval generator
"""

from generate_narrative_intervals import NarrativeIntervalGenerator
import os

def main():
    # Example usage
    narrative_file = "nlpv2/nlp_outputs/narrative_20250621_205640.txt"
    stream_dir = "stream_processed_clip"
    
    # Check if files exist
    if not os.path.exists(narrative_file):
        print(f"Narrative file not found: {narrative_file}")
        print("Please provide a valid narrative file path")
        return
    
    if not os.path.exists(stream_dir):
        print(f"Stream directory not found: {stream_dir}")
        print("Please ensure the processed stream files are in the correct directory")
        return
    
    # Different total video duration examples
    durations = [180, 300, 420]  # 3min, 5min, 7min total video lengths
    
    for duration in durations:
        print(f"\n{'='*70}")
        print(f"Generating dynamic intervals for {duration//60}min {duration%60}s total video")
        print(f"{'='*70}")
        
        try:
            generator = NarrativeIntervalGenerator(
                narrative_file=narrative_file,
                stream_dir=stream_dir,
                total_duration=duration
            )
            
            output_file = f"demo_intervals_{duration//60}min_{duration%60}s.json"
            generator.generate_intervals(output_file)
            
        except Exception as e:
            print(f"Error generating intervals for {duration}s total: {e}")
            continue

if __name__ == "__main__":
    main() 