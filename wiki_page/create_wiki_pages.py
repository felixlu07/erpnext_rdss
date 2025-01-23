import os
import csv
import json
import requests
from collections import defaultdict
from dotenv import load_dotenv

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Load environment variables from parent directory
load_dotenv(os.path.join(parent_dir, '.env'))

# ERPNext credentials
api_key = os.getenv('ERPNEXT_RDSS_API_KEY')
api_secret = os.getenv('ERPNEXT_RDSS_API_SECRET')
erpnext_url = os.getenv('ERPNEXT_RDSS_URL')

def get_wiki_space():
    """Get or create the Wiki Space for rare diseases"""
    headers = {
        'Authorization': f'token {api_key}:{api_secret}',
        'Content-Type': 'application/json',
    }
    
    try:
        # Check if space exists
        response = requests.get(
            f'{erpnext_url}/api/resource/Wiki Space?filters={{"route":"wiki/rare-diseases"}}',
            headers=headers
        )
        
        if response.status_code == 200:
            existing_spaces = response.json().get('data', [])
            if existing_spaces:
                return existing_spaces[0].get('name')
        
        # Create new space if it doesn't exist
        space_data = {
            "doctype": "Wiki Space",
            "name": "rare-diseases",
            "title": "Rare Diseases",
            "route": "wiki/rare-diseases",
            "published": 1,
            "is_active": 1,
            "allow_guest": 1,
            "allow_edit": 0,
            "available_for_portal_users": 1
        }
        
        response = requests.post(
            f'{erpnext_url}/api/resource/Wiki Space',
            headers=headers,
            json=space_data
        )
        
        response.raise_for_status()
        result = response.json()
        return result.get('data', {}).get('name')
        
    except requests.exceptions.RequestException as e:
        print(f"Error with Wiki Space: {str(e)}")
        return None

def format_title(filename):
    """Convert markdown filename to readable title"""
    # Remove .md extension
    title = filename.replace('.md', '')
    # Replace underscores with spaces
    title = title.replace('_', ' ')
    return title

def create_index_page(letter, diseases, space_name):
    """Create content for index page of a letter"""
    content = f"# Diseases Starting with {letter}\n\n"
    for disease in sorted(diseases):
        content += f"- [{disease}](/wiki/{disease.replace(' ', '_')})\n"
    
    page_data = {
        'doctype': 'Wiki Page',
        'title': f'Diseases - {letter}',
        'route': f'wiki/diseases_{letter.lower()}',
        'content': content,
        'published': 1,
        'allow_guest': 1,
        'wiki_space': space_name,
        'show_sidebar': 1,
        'description': f'List of rare diseases starting with {letter}',
        'keywords': f'rare diseases, diseases {letter}, index'
    }
    
    create_wiki_page(page_data)

def create_wiki_page(data):
    """Create a wiki page in ERPNext using the API"""
    headers = {
        'Authorization': f'token {api_key}:{api_secret}',
        'Content-Type': 'application/json',
    }
    
    try:
        # Check if page already exists
        route = data['route']
        response = requests.get(
            f'{erpnext_url}/api/resource/Wiki Page?filters={{"route":"{route}"}}',
            headers=headers
        )
        
        if response.status_code == 200:
            existing_pages = response.json().get('data', [])
            if existing_pages:
                # Update existing page with space
                page_name = existing_pages[0].get('name')
                if page_name and 'wiki_space' in data:
                    update_response = requests.put(
                        f'{erpnext_url}/api/resource/Wiki Page/{page_name}',
                        headers=headers,
                        json={"wiki_space": data['wiki_space']}
                    )
                    if update_response.status_code == 200:
                        print(f"Updated Wiki Space for: {data['title']}")
                return True
        
        # Create new page
        response = requests.post(
            f'{erpnext_url}/api/resource/Wiki Page',
            headers=headers,
            json=data
        )
        
        if response.status_code == 409:  # Conflict
            print(f"Page already exists (409): {data['title']}")
            return True
            
        response.raise_for_status()
        print(f"Successfully created page: {data['title']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating page {data['title']}: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False

def main():
    # Get or create Wiki Space
    space_name = get_wiki_space()
    if not space_name:
        print("Failed to get or create Wiki Space. Aborting.")
        return
        
    docs_dir = os.path.join(current_dir, 'docs')
    
    # Group diseases by first letter
    diseases_by_letter = defaultdict(list)
    
    # First, read all markdown files and organize them
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md') and filename != 'Intro.md':
            title = format_title(filename)
            first_letter = title[0].upper()
            diseases_by_letter[first_letter].append(title)
            
            # Read the markdown content
            with open(os.path.join(docs_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create individual disease page
            page_data = {
                'doctype': 'Wiki Page',
                'title': title,
                'route': f'wiki/{title.replace(" ", "_")}',
                'content': content,
                'published': 1,
                'allow_guest': 1,
                'wiki_space': space_name,
                'show_sidebar': 1,
                'description': f'Information about {title}',
                'keywords': f'rare disease, {title.lower()}'
            }
            
            create_wiki_page(page_data)
    
    # Create index pages for each letter
    for letter, diseases in diseases_by_letter.items():
        create_index_page(letter, diseases, space_name)
    
    # Create main index page
    main_content = "# Rare Diseases Index\n\nBrowse diseases by first letter:\n\n"
    for letter in sorted(diseases_by_letter.keys()):
        main_content += f"- [{letter}](/wiki/diseases_{letter.lower()}) ({len(diseases_by_letter[letter])} diseases)\n"
    
    main_page_data = {
        'doctype': 'Wiki Page',
        'title': 'Rare Diseases Directory',
        'route': 'wiki/rare_diseases',
        'content': main_content,
        'published': 1,
        'allow_guest': 1,
        'wiki_space': space_name,
        'show_sidebar': 1,
        'description': 'Directory of rare diseases organized alphabetically',
        'keywords': 'rare diseases, disease directory, index'
    }
    
    create_wiki_page(main_page_data)

if __name__ == '__main__':
    main()
