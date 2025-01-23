import os
import json
import anthropic
from dotenv import load_dotenv
import time

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Load environment variables
load_dotenv(os.path.join(parent_dir, '.env'))

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def get_structured_content(condition_name, existing_content):
    """Use Claude to structure/supplement content according to our template"""
    
    prompt = f"""Please restructure and supplement the following medical condition information into a standardized format.
If any sections are missing information, please supplement with accurate medical knowledge.
Use this exact structure with these exact headers:

# {condition_name}

### Disease Overview

### Disease Category

### Synonyms

### Signs & Symptoms

### Causes

### Affected Populations

### Disorders with Similar Symptoms

### Diagnosis

### Standard Therapies

### Clinical Trials and Studies

### References

### Programs & Resources

### Complete Report

Here is the existing content to restructure and supplement:

{existing_content}

Please ensure all sections are present and contain accurate information, even if you need to supplement missing sections with medical knowledge. Maintain a professional, medical tone throughout."""

    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model=os.getenv('ANTHROPIC_MODEL', 'claude-3-5-haiku-20241022'),
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0
            )
            
            # Extract the content from the response
            if hasattr(message, 'content') and len(message.content) > 0:
                # Get the first content block's text
                content = message.content[0].text if isinstance(message.content, list) else message.content
                return content
            else:
                print(f"No content in response for {condition_name}")
                return None
            
        except anthropic.APIError as e:
            print(f"API Error on attempt {attempt + 1} for {condition_name}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                print(f"Failed after {max_retries} attempts")
                return None
                
        except Exception as e:
            print(f"Unexpected error processing {condition_name}: {str(e)}")
            return None

def restructure_files():
    """Restructure all markdown files in the docs directory"""
    docs_dir = os.path.join(current_dir, 'docs')
    
    # Create backup directory
    backup_dir = os.path.join(docs_dir, 'backup')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Process each markdown file
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(docs_dir, filename)
            
            # Skip if it's in the backup directory
            if 'backup' in file_path:
                continue
            
            print(f"\nProcessing {filename}...")
            
            try:
                # Read existing content
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # Create backup
                backup_path = os.path.join(backup_dir, filename)
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(existing_content)
                
                # Get condition name from filename
                condition_name = filename.replace('.md', '').replace('_', ' ')
                
                # Get restructured content
                new_content = get_structured_content(condition_name, existing_content)
                
                if new_content:
                    # Write new content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(str(new_content))  # Ensure content is string
                    print(f"Successfully restructured {filename}")
                else:
                    print(f"Failed to restructure {filename}")
            
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue

if __name__ == '__main__':
    print("Starting content restructuring...")
    restructure_files()
    print("\nContent restructuring complete!")
