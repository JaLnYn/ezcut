#!/usr/bin/env python3
"""
Example usage of NLP v2 system for generating narratives from processed video content.
"""

import os
from main import read_file_raw, read_folder_raw, generate_narrative

def process_file(file_path: str, api_key: str = None):
    """Process a single file and generate narrative."""
    print(f"Processing file: {file_path}")
    
    # Read the file as raw text
    content = read_file_raw(file_path)
    print(f"Read {len(content)} characters")
    
    if not content:
        print("No content found in file")
        return
    
    # Generate narrative
    print("Generating narrative...")
    narrative = generate_narrative(content, api_key)
    
    # Output results
    print("\n" + "="*60)
    print("GENERATED NARRATIVE")
    print("="*60)
    print(narrative)
    print("="*60)
    
    return narrative

def process_folder(folder_path: str, api_key: str = None):
    """Process all txt files in a folder and generate narrative."""
    print(f"Processing folder: {folder_path}")
    
    # Read all files as raw text
    content = read_folder_raw(folder_path)
    print(f"Combined content: {len(content)} characters")
    
    if not content:
        print("No content found in folder")
        return
    
    # Generate narrative
    print("Generating narrative...")
    narrative = generate_narrative(content, api_key)
    
    # Output results
    print("\n" + "="*60)
    print("GENERATED NARRATIVE")
    print("="*60)
    print(narrative)
    print("="*60)
    
    return narrative

def main():
    """Main example function."""
    # You can set your API key here or use environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Example 1: Process a single file
    single_file = "../stream_processed/part1_processed.txt"
    if os.path.exists(single_file):
        print("EXAMPLE 1: Processing single file")
        print("-" * 40)
        narrative1 = process_file(single_file, api_key)
        print()
    
    # Example 2: Process a folder
    folder_path = "../outputs"
    if os.path.exists(folder_path):
        print("EXAMPLE 2: Processing folder")
        print("-" * 40)
        narrative2 = process_folder(folder_path, api_key)
        
        # Save the folder narrative
        if narrative2 and not narrative2.startswith("Error"):
            output_file = "generated_narrative_from_folder.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(narrative2)
            print(f"\nNarrative saved to: {output_file}")
    else:
        print(f"Folder not found: {folder_path}")

if __name__ == "__main__":
    main() 