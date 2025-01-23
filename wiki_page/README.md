# RDSS Wiki Page Management System

This directory contains scripts for managing the RDSS Wiki system in ERPNext. The system is designed to create and maintain a structured wiki for rare diseases information.

## System Overview

The wiki system consists of:
- A Wiki Space that serves as the container for all pages
- Wiki Pages organized in a hierarchical structure
- A sidebar navigation system using Wiki Group Items

## File Structure

```
wiki_page/
├── docs/           # Contains markdown files for each disease
├── rebuild_wiki.py # Main script to rebuild the entire wiki
└── README.md      # This documentation
```

## Scripts

### rebuild_wiki.py

Main script that handles:
1. Deleting existing wiki content
2. Creating new pages
3. Setting up the Wiki Space with proper sidebar structure

Key functions:
- `delete_all_wiki_content()`: Removes existing Wiki Pages and Spaces
- `create_wiki_page()`: Creates individual Wiki Pages
- `create_wiki_space_with_pages()`: Creates Wiki Space with sidebar configuration

## Wiki Structure

The wiki is organized as follows:

```
Navigation
├── Home
└── Disease Directory

Diseases A-Z
├── A
│   ├── Disease Page 1
│   └── Disease Page 2
├── B
│   ├── Disease Page 3
│   └── Disease Page 4
└── ...
```

## ERPNext API Structure

### Wiki Space Payload

```json
{
    "doctype": "Wiki Space",
    "route": "wiki/rare-diseases",
    "wiki_sidebars": [
        {
            "doctype": "Wiki Group Item",
            "parent_label": "Category Name",
            "wiki_page": "page_id",
            "hide_on_sidebar": 0
        }
    ]
}
```

### Wiki Page Payload

```json
{
    "doctype": "Wiki Page",
    "title": "Page Title",
    "route": "wiki/page-route",
    "content": "Page Content",
    "wiki_space": "space_id",
    "published": 1,
    "allow_guest": 1,
    "show_sidebar": 1
}
```

## Environment Variables

Required environment variables in `.env` file:
- `ERPNEXT_RDSS_API_KEY`: API key for ERPNext
- `ERPNEXT_RDSS_API_SECRET`: API secret for ERPNext
- `ERPNEXT_RDSS_URL`: Base URL for ERPNext instance

## Usage

1. Ensure all environment variables are set in the parent directory's `.env` file
2. Place disease markdown files in the `docs/` directory
3. Run the rebuild script:
   ```bash
   python rebuild_wiki.py
   ```

## Important Notes

1. **Page IDs**: Each Wiki Page gets a unique ID from ERPNext. These IDs are used in the Wiki Space sidebar configuration.

2. **Sidebar Structure**: Pages must be properly registered in the Wiki Space's sidebar configuration to appear in the navigation.

3. **Content Organization**: 
   - The home page provides the main navigation
   - Letter index pages list diseases starting with each letter
   - Individual disease pages contain the detailed information

4. **Error Handling**:
   - The script includes comprehensive error handling
   - Failed operations are logged with error messages
   - The script can be safely re-run as it cleans up existing content first

## Troubleshooting

Common issues and solutions:

1. **Missing Pages in Sidebar**
   - Ensure the page ID is correctly added to the Wiki Space sidebar configuration
   - Check that the page was successfully created before adding to sidebar

2. **API Errors**
   - Verify environment variables are correct
   - Check API key permissions in ERPNext
   - Ensure proper network connectivity to ERPNext server

3. **Content Not Showing**
   - Verify the markdown file exists in `docs/` directory
   - Check file encoding (should be UTF-8)
   - Ensure content was properly loaded and sent in the API request

## Maintenance

To update the wiki:
1. Add/modify markdown files in the `docs/` directory
2. Run `rebuild_wiki.py` to update the entire wiki structure

The script is designed to be idempotent - it can be run multiple times safely as it cleans up existing content before creating new pages.
