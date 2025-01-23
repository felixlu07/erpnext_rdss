import os
import json
import requests
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

def create_wiki_space():
    """Create a Wiki Space for rare diseases"""
    headers = {
        'Authorization': f'token {api_key}:{api_secret}',
        'Content-Type': 'application/json',
    }
    
    space_data = {
        "doctype": "Wiki Space",
        "name": "rare-diseases",
        "title": "Rare Diseases",
        "route": "wiki/rare-diseases",
        "published": 1,
        "is_active": 1,
        "allow_guest": 1,
        "allow_edit": 0,  # Only admins can edit
        "available_for_portal_users": 1
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
                print("Wiki Space already exists")
                return existing_spaces[0].get('name')
        
        # Create new space
        response = requests.post(
            f'{erpnext_url}/api/resource/Wiki Space',
            headers=headers,
            json=space_data
        )
        
        response.raise_for_status()
        result = response.json()
        print("Successfully created Wiki Space")
        return result.get('data', {}).get('name')
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating Wiki Space: {str(e)}")
        return None

def create_wiki_page(data, space_name):
    """Create a wiki page in ERPNext using the API"""
    headers = {
        'Authorization': f'token {api_key}:{api_secret}',
        'Content-Type': 'application/json',
    }
    
    # Add Wiki Space to page data
    data['wiki_space'] = space_name
    data['doctype'] = 'Wiki Page'
    
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
                print(f"Page already exists: {data['title']}")
                # Update existing page with space
                page_name = existing_pages[0].get('name')
                if page_name:
                    update_response = requests.put(
                        f'{erpnext_url}/api/resource/Wiki Page/{page_name}',
                        headers=headers,
                        json={"wiki_space": space_name}
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
        
        response.raise_for_status()
        print(f"Successfully created page: {data['title']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating page {data['title']}: {str(e)}")
        return False

def create_wiki_sidebar(space_name):
    """Create a Wiki Page Sidebar for navigation"""
    headers = {
        'Authorization': f'token {api_key}:{api_secret}',
        'Content-Type': 'application/json',
    }
    
    sidebar_data = {
        "doctype": "Wiki Sidebar",
        "title": "Rare Diseases Navigation",
        "wiki_space": space_name,
        "sidebar_items": [
            {
                "title": "Home",
                "route": "/wiki/home",
                "group_name": "Navigation"
            },
            {
                "title": "Disease Directory",
                "route": "/wiki/rare_diseases",
                "group_name": "Navigation"
            },
            {
                "title": "Browse by Letter",
                "group_name": "Diseases A-Z",
                "is_group": 1
            }
        ]
    }
    
    # Add A-Z links to sidebar
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        sidebar_data["sidebar_items"].append({
            "title": f"Diseases - {letter}",
            "route": f"/wiki/diseases_{letter.lower()}",
            "group_name": "Diseases A-Z"
        })
    
    try:
        response = requests.post(
            f'{erpnext_url}/api/resource/Wiki Sidebar',
            headers=headers,
            json=sidebar_data
        )
        
        response.raise_for_status()
        print("Successfully created Wiki Sidebar")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating sidebar: {str(e)}")
        return False

def create_home_page(space_name):
    """Create the main landing page for the wiki"""
    content = """# Welcome to RDSS Rare Diseases Wiki

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

    page_data = {
        'title': 'RDSS Wiki Home',
        'route': 'wiki/home',
        'content': content,
        'published': 1,
        'allow_guest': 1,
        'show_sidebar': 1,
        'description': 'Welcome to the RDSS Rare Diseases Wiki',
        'keywords': 'rare diseases, RDSS, wiki, home'
    }
    
    return create_wiki_page(page_data, space_name)

def main():
    # First create the Wiki Space
    space_name = create_wiki_space()
    if not space_name:
        print("Failed to create or get Wiki Space. Aborting.")
        return
    
    # Create the sidebar for navigation
    create_wiki_sidebar(space_name)
    
    # Create the home page
    create_home_page(space_name)
    
    print("\nSetup complete! You can now access the wiki at:")
    print(f"{erpnext_url}/wiki/home")
    print("\nMake sure to:")
    print("1. Log into ERPNext")
    print("2. Go to Wiki Space list")
    print("3. Verify the 'Rare Diseases' space is active")
    print("4. Check that all pages are properly associated with the space")

if __name__ == '__main__':
    main()
