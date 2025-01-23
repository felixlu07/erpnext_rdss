import os
import json
import requests
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Load environment variables from parent directory
load_dotenv(os.path.join(parent_dir, '.env'))

# ERPNext credentials
api_key = os.getenv('ERPNEXT_RDSS_API_KEY')
api_secret = os.getenv('ERPNEXT_RDSS_API_SECRET')
erpnext_url = os.getenv('ERPNEXT_RDSS_URL')

def get_headers():
    """Get API headers"""
    return {
        'Authorization': f'token {api_key}:{api_secret}',
        'Content-Type': 'application/json',
    }

def delete_all_wiki_content():
    """Delete all existing wiki pages and spaces"""
    headers = get_headers()
    
    # Delete Wiki Pages
    try:
        response = requests.get(
            f'{erpnext_url}/api/resource/Wiki Page?fields=["name"]&limit_page_length=None',
            headers=headers
        )
        if response.status_code == 200:
            pages = response.json().get('data', [])
            for page in pages:
                delete_response = requests.delete(
                    f'{erpnext_url}/api/resource/Wiki Page/{page["name"]}',
                    headers=headers
                )
                if delete_response.status_code == 202:
                    print(f"Deleted Wiki Page: {page['name']}")
    except Exception as e:
        print(f"Error deleting Wiki Pages: {str(e)}")

    # Delete Wiki Spaces
    try:
        response = requests.get(
            f'{erpnext_url}/api/resource/Wiki Space?fields=["name"]&limit_page_length=None',
            headers=headers
        )
        if response.status_code == 200:
            spaces = response.json().get('data', [])
            for space in spaces:
                delete_response = requests.delete(
                    f'{erpnext_url}/api/resource/Wiki Space/{space["name"]}',
                    headers=headers
                )
                if delete_response.status_code == 202:
                    print(f"Deleted Wiki Space: {space['name']}")
    except Exception as e:
        print(f"Error deleting Wiki Spaces: {str(e)}")

def create_wiki_page(data, space_name):
    """Create a wiki page and associate it with the space"""
    headers = get_headers()
    
    # Add Wiki Space to page data
    data['doctype'] = 'Wiki Page'
    data['wiki_space'] = space_name
    data['published'] = 1
    data['allow_guest'] = 1
    data['show_sidebar'] = 1
    
    try:
        response = requests.post(
            f'{erpnext_url}/api/resource/Wiki Page',
            headers=headers,
            json=data
        )
        
        response.raise_for_status()
        result = response.json()
        page_name = result.get('data', {}).get('name')
        print(f"Created page: {data['title']} ({page_name})")
        return page_name
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating page {data['title']}: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def create_wiki_space_with_pages(pages_by_category):
    """Create Wiki Space with proper sidebar structure"""
    headers = get_headers()
    
    # Prepare Wiki Space data
    space_data = {
        "doctype": "Wiki Space",
        "route": "wiki/rare-diseases",
        "wiki_sidebars": []
    }
    
    # Add navigation pages to sidebar
    for category, pages in pages_by_category.items():
        # Add category as parent label
        for page_name, page_info in pages.items():
            sidebar_item = {
                "doctype": "Wiki Group Item",
                "parent_label": category,
                "wiki_page": page_info['id'],
                "hide_on_sidebar": 0
            }
            space_data["wiki_sidebars"].append(sidebar_item)
    
    try:
        response = requests.post(
            f'{erpnext_url}/api/resource/Wiki Space',
            headers=headers,
            json=space_data
        )
        
        response.raise_for_status()
        result = response.json()
        space_name = result.get('data', {}).get('name')
        print(f"Created Wiki Space: {space_name}")
        return space_name
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating Wiki Space: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def format_title(filename):
    """Convert markdown filename to readable title"""
    title = filename.replace('.md', '').replace('_', ' ')
    return title

def main():
    print("Step 1: Deleting existing wiki content...")
    delete_all_wiki_content()
    
    print("\nStep 2: Creating pages...")
    docs_dir = os.path.join(current_dir, 'docs')
    pages_by_category = {
        'Navigation': {},
        'Diseases A-Z': {}
    }
    
    # Create home page
    home_content = """# Welcome to RDSS Rare Diseases Wiki

Welcome to the Rare Diseases Support Singapore (RDSS) Wiki, your comprehensive resource for information about rare diseases. This wiki serves as a knowledge repository to help patients, families, and healthcare providers better understand various rare conditions.

## Quick Navigation

- [Browse Disease Directory](/wiki/rare_diseases) - View all diseases organized alphabetically
- [About RDSS](/wiki/about_rdss) - Learn more about Rare Diseases Support Singapore

## Browse by Letter

Browse diseases by their first letter:

| A-E | F-J | K-O | P-T | U-Z |
|-----|-----|-----|-----|-----|
| [A](/wiki/diseases_a) | [F](/wiki/diseases_f) | [K](/wiki/diseases_k) | [P](/wiki/diseases_p) | [U](/wiki/diseases_u) |
| [B](/wiki/diseases_b) | [G](/wiki/diseases_g) | [L](/wiki/diseases_l) | [Q](/wiki/diseases_q) | [V](/wiki/diseases_v) |
| [C](/wiki/diseases_c) | [H](/wiki/diseases_h) | [M](/wiki/diseases_m) | [R](/wiki/diseases_r) | [W](/wiki/diseases_w) |
| [D](/wiki/diseases_d) | [I](/wiki/diseases_i) | [N](/wiki/diseases_n) | [S](/wiki/diseases_s) | [X](/wiki/diseases_x) |
| [E](/wiki/diseases_e) | [J](/wiki/diseases_j) | [O](/wiki/diseases_o) | [T](/wiki/diseases_t) | [Y-Z](/wiki/diseases_z) |

## Recent Updates

Check our [Recent Updates](/wiki/recent_updates) page to see the latest additions and changes to the wiki.

## Contributing

If you would like to contribute to this wiki or have information about a rare disease that's not listed, please contact RDSS."""

    home_page_id = create_wiki_page({
        'title': 'RDSS Wiki Home',
        'route': 'wiki/home',
        'content': home_content,
        'description': 'Welcome to the RDSS Rare Diseases Wiki',
        'keywords': 'rare diseases, RDSS, wiki, home'
    }, None)
    
    if home_page_id:
        pages_by_category['Navigation']['home'] = {
            'id': home_page_id,
            'title': 'Home'
        }
    
    # Create disease pages and organize by letter
    diseases_by_letter = defaultdict(list)
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md') and filename != 'Intro.md':
            title = format_title(filename)
            first_letter = title[0].upper()
            
            with open(os.path.join(docs_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()
            
            page_id = create_wiki_page({
                'title': title,
                'route': f'wiki/{title.replace(" ", "_")}',
                'content': content,
                'description': f'Information about {title}',
                'keywords': f'rare disease, {title.lower()}'
            }, None)
            
            if page_id:
                diseases_by_letter[first_letter].append({
                    'id': page_id,
                    'title': title
                })
    
    # Create letter index pages
    for letter, diseases in diseases_by_letter.items():
        content = f"# Diseases Starting with {letter}\n\n"
        for disease in sorted(diseases, key=lambda x: x['title']):
            content += f"- [{disease['title']}](/wiki/{disease['title'].replace(' ', '_')})\n"
        
        page_id = create_wiki_page({
            'title': f'Diseases - {letter}',
            'route': f'wiki/diseases_{letter.lower()}',
            'content': content,
            'description': f'List of rare diseases starting with {letter}',
            'keywords': f'rare diseases, diseases {letter}, index'
        }, None)
        
        if page_id:
            pages_by_category['Diseases A-Z'][f'letter_{letter}'] = {
                'id': page_id,
                'title': f'Diseases - {letter}'
            }
            
            # Add disease pages under this letter
            for disease in diseases:
                pages_by_category['Diseases A-Z'][disease['title']] = {
                    'id': disease['id'],
                    'title': disease['title']
                }
    
    print("\nStep 3: Creating Wiki Space with sidebar structure...")
    space_name = create_wiki_space_with_pages(pages_by_category)
    
    if space_name:
        print("\nWiki rebuild complete! You can now access the wiki at:")
        print(f"{erpnext_url}/wiki/home")
    else:
        print("\nFailed to create Wiki Space. Please check the errors above.")

if __name__ == '__main__':
    main()
