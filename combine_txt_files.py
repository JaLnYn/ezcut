#!/usr/bin/env python3
"""
Script to combine all txt files in a folder into a single file.
For each txt file, it writes the filename followed by the content.
"""

import os
import argparse
from pathlib import Path


def combine_txt_files(input_folder, output_file):
    """
    Combine all txt files in the input folder into a single output file.
    
    Args:
        input_folder (str): Path to the folder containing txt files
        output_file (str): Path to the output file to create
    """
    input_path = Path(input_folder)
    
    if not input_path.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return
    
    if not input_path.is_dir():
        print(f"Error: '{input_folder}' is not a directory.")
        return
    
    # Find all txt files in the folder
    txt_files = list(input_path.glob("*.txt"))
    
    if not txt_files:
        print(f"No txt files found in '{input_folder}'.")
        return
    
    print(f"Found {len(txt_files)} txt files in '{input_folder}'.")
    
    # Sort files for consistent output
    txt_files.sort()
    
    # Write combined content to output file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for txt_file in txt_files:
            print(f"Processing: {txt_file.name}")
            
            # Write filename
            outfile.write(f"filename: {txt_file.name}\n")
            outfile.write("-" * 50 + "\n")
            
            # Write file content
            try:
                with open(txt_file, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    
                    # Add newline if content doesn't end with one
                    if content and not content.endswith('\n'):
                        outfile.write('\n')
                        
            except Exception as e:
                outfile.write(f"Error reading file: {e}\n")
            
            # Add separator between files
            outfile.write("\n" + "=" * 80 + "\n\n")
    
    print(f"Successfully combined {len(txt_files)} files into '{output_file}'.")


def main():
    parser = argparse.ArgumentParser(
        description="Combine all txt files in a folder into a single file"
    )
    parser.add_argument(
        "input_folder",
        help="Path to the folder containing txt files"
    )
    parser.add_argument(
        "-o", "--output",
        default="combined_output.txt",
        help="Output file name (default: combined_output.txt)"
    )
    
    args = parser.parse_args()
    
    combine_txt_files(args.input_folder, args.output)


if __name__ == "__main__":
    main() 