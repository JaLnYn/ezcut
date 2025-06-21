#!/usr/bin/env python3
"""
Simple script to assemble the vlog from vlog_script.txt
"""

from vlog_assembler import VlogAssembler

def main():
    # Create the assembler
    assembler = VlogAssembler(videos_dir="videos", output_dir="outputs")
    
    # First, create a summary to see what we're working with
    print("Creating script summary...")
    assembler.create_script_summary("vlog_script.txt")
    
    # Now assemble the final vlog
    print("\nAssembling final vlog...")
    success = assembler.assemble_vlog("vlog_script.txt", "hackai_toronto_vlog.mp4")
    
    if success:
        print("\n🎉 Vlog assembly complete!")
        print("Check the outputs/ folder for:")
        print("- hackai_toronto_vlog.mp4 (final video)")
        print("- vlog_summary.txt (script summary)")
    else:
        print("\n❌ Vlog assembly failed. Check the error messages above.")

if __name__ == "__main__":
    main() 