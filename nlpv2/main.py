import os
import openai
import glob

def read_file_raw(file_path: str) -> str:
    """Read the entire file as raw text."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def read_folder_raw(folder_path: str) -> str:
    """Read all txt files in a folder and combine them."""
    all_content = []
    
    # Get all txt files in the folder
    txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
    
    if not txt_files:
        print(f"No txt files found in {folder_path}")
        return ""
    
    print(f"Found {len(txt_files)} txt files:")
    for file_path in txt_files:
        filename = os.path.basename(file_path)
        print(f"  - {filename}")
        
        # Read each file
        content = read_file_raw(file_path)
        all_content.append(f"\n--- {filename} ---\n{content}")
    
    return "\n".join(all_content)

def generate_narrative(file_content: str, api_key: str = None) -> str:
    """Generate narrative using OpenAI API with raw file content."""
    if api_key:
        client = openai.OpenAI(api_key=api_key)
    else:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    if not client.api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
    
    prompt = f"""Based on this video content (keyframes and transcripts from multiple files), create a short, engaging summary (2-3 paragraphs) that captures the essence of this stream/vlog content. Make it entertaining and conversational:

{file_content}

Create a short narrative that flows naturally from this content:"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative writer who creates engaging, short-form narratives from video content. Keep responses concise and entertaining."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating narrative: {str(e)}"

def main():
    """Main function to process a folder and generate narrative."""
    # Process the outputs folder
    folder_path = "../outputs"
    
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return
    
    print("Reading all txt files from folder...")
    content = read_folder_raw(folder_path)
    print(f"Combined content: {len(content)} characters")
    
    if not content:
        print("No content found")
        return
    
    print("Generating narrative with OpenAI...")
    narrative = generate_narrative(content)
    
    print("\n" + "="*50)
    print("GENERATED NARRATIVE:")
    print("="*50)
    print(narrative)
    print("="*50)

if __name__ == "__main__":
    main()
