# NLP v2 - Simple Narrative Generator

A minimal system that reads processed video content (keyframes + transcripts) and generates short narratives using OpenAI.

## Setup

1. Install dependencies:

```bash
# From the project root directory
pip install -r requirements.txt
```

2. Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage

Run the main script (processes all txt files in the outputs folder):

```bash
python nlpv2/main.py
```

Or use the example script (shows both single file and folder processing):

```bash
python nlpv2/example.py
```

### Custom Usage

```python
from nlpv2.main import read_file_raw, read_folder_raw, generate_narrative

# Process a single file
content = read_file_raw("path/to/your/file.txt")
narrative = generate_narrative(content)

# Process all txt files in a folder
content = read_folder_raw("path/to/your/folder")
narrative = generate_narrative(content)

print(narrative)
```

## Input Format

The system expects processed text files with this format:

```
[keyframe:00:00:00] Visual description of the scene...
[transcript:00:00:06] Spoken content...
[transcript:00:00:12] More spoken content...
[keyframe:00:00:30] Next visual description...
[transcript:00:00:38] More spoken content...
```

## Folder Processing

When processing a folder, the system:

- Finds all `.txt` files in the specified folder
- Combines them with clear separators
- Sends the entire combined content to OpenAI
- Generates a narrative that covers all the content

## Output

The system generates a short, engaging narrative (2-3 paragraphs) that captures the essence of the video content in a conversational style.

## Configuration

- `max_tokens`: Control the length of generated narrative (default: 300)
- `temperature`: Control creativity vs consistency (default: 0.7)

## Files

- `main.py`: Core functionality
- `example.py`: Example usage (single file + folder processing)
- `README.md`: This file
