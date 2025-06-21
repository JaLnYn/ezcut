#!/bin/bash

# Enhanced video processor script
# - Splits videos into 30-second chunks
# - Extracts audio separately
# - Captures frames at 20%, 50%, 80% of video duration

# Check if directory argument is provided
if [ $# -eq 1 ]; then
    VIDEO_DIR="$1"
    if [ ! -d "$VIDEO_DIR" ]; then
        echo "Error: Directory '$VIDEO_DIR' does not exist!"
        exit 1
    fi
    echo "Processing videos in: $VIDEO_DIR"
    cd "$VIDEO_DIR"
else
    VIDEO_DIR="$(pwd)"
    echo "Processing videos in current directory: $VIDEO_DIR"
fi

# Create output directory if it doesn't exist
mkdir -p processed_videos

# Counter for progress
count=0
total=$(find . -maxdepth 1 \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.avi" -o -iname "*.mkv" -o -iname "*.wmv" -o -iname "*.flv" -o -iname "*.webm" \) | wc -l)

echo "Found $total video files to process..."

# Function to get video duration in seconds
get_duration() {
    ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$1"
}

# Function to format timestamp
format_time() {
    printf "%02d:%02d:%02d" $((${1%.*}/3600)) $((${1%.*}%3600/60)) $((${1%.*}%60))
}

# Process each video file
for video in *.{mp4,mov,avi,mkv,wmv,flv,webm}; do
    # Skip if file doesn't exist (handles case where no files match pattern)
    [[ ! -f "$video" ]] && continue
    
    count=$((count + 1))
    echo "[$count/$total] Processing: $video"
    
    # Get filename without extension
    filename="${video%.*}"
    
    # Create subdirectory for this video's output
    output_dir="processed_videos/${filename}"
    mkdir -p "$output_dir/chunks"
    mkdir -p "$output_dir/audio"
    mkdir -p "$output_dir/frames"
    
    # Get video duration
    duration=$(get_duration "$video")
    if [ -z "$duration" ] || [ "$duration" = "N/A" ]; then
        echo "✗ Could not get duration for $video, skipping..."
        continue
    fi
    
    echo "  Duration: $(format_time $duration)"
    
    # Calculate frame extraction times (20%, 50%, 80%)
    time_20=$(echo "$duration * 0.2" | bc)
    time_50=$(echo "$duration * 0.5" | bc)
    time_80=$(echo "$duration * 0.8" | bc)
    
    echo "  Extracting frames at: $(format_time $time_20), $(format_time $time_50), $(format_time $time_80)"
    
    # Extract frames at 20%, 50%, 80%
    ffmpeg -i "$video" -ss "$time_20" -vframes 1 -q:v 2 "$output_dir/frames/${filename}_20percent.jpg" -loglevel error
    ffmpeg -i "$video" -ss "$time_50" -vframes 1 -q:v 2 "$output_dir/frames/${filename}_50percent.jpg" -loglevel error
    ffmpeg -i "$video" -ss "$time_80" -vframes 1 -q:v 2 "$output_dir/frames/${filename}_80percent.jpg" -loglevel error
    
    # Extract audio
    echo "  Extracting audio..."
    ffmpeg -i "$video" -vn -acodec copy "$output_dir/audio/${filename}.aac" -loglevel error 2>/dev/null
    if [ $? -ne 0 ]; then
        # Try with mp3 if original codec fails
        ffmpeg -i "$video" -vn -acodec mp3 -ab 192k "$output_dir/audio/${filename}.mp3" -loglevel error
    fi
    
    # Split video into 30-second chunks
    echo "  Splitting into 30-second chunks..."
    ffmpeg -i "$video" -c copy -segment_time 30 -f segment -reset_timestamps 1 \
           "$output_dir/chunks/${filename}_%03d.mp4" \
           -loglevel error -stats
    
    if [ $? -eq 0 ]; then
        # Count created chunks
        chunk_count=$(ls "$output_dir/chunks/"*.mp4 2>/dev/null | wc -l)
        echo "✓ Successfully processed $video"
        echo "  Created: $chunk_count video chunks, 1 audio file, 3 frame captures"
    else
        echo "✗ Error processing $video"
    fi
    
    echo ""
done

echo "All videos processed! Check the 'processed_videos' directory for results."
echo ""
echo "Output structure for each video:"
echo "  video_name/"
echo "  ├── chunks/     (30-second video segments)"
echo "  ├── audio/      (extracted audio)"
echo "  └── frames/     (20%, 50%, 80% frame captures)"
