# RDSS ERPNext Integration

This repository contains the integration scripts and content management system for Rare Disease Support Singapore (RDSS) with ERPNext.

## Project Structure

```
erpnext_rdss/
├── wiki_page/              # Wiki page management
│   ├── docs/              # Source markdown files for diseases
│   ├── create_wiki_structure.py  # Wiki space creation
│   ├── create_wiki_pages.py      # Individual page creation
│   ├── rebuild_wiki.py           # Complete wiki rebuild
│   └── restructure_content.py    # Content standardization
├── patient_management/    # Patient data management
└── .env                  # Environment configuration
```

## Features

### Wiki System
- Structured disease information pages
- Hierarchical navigation system
- Standardized content format for all diseases
- Automatic content restructuring with AI assistance

### Patient Management
- Patient data import/export
- Story management
- Data validation and cleaning

## Setup

1. Clone the repository
2. Create a `.env` file with the following variables:
   ```
   ERPNEXT_RDSS_API_KEY=your_api_key
   ERPENEXT_RDSS_LOGIN=your_login
   ERPNEXT_RDSS_PASSWORD=your_password
   ERPNEXT_RDSS_URL=your_erpnext_url
   ```
3. Install dependencies:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Usage

### Wiki Management

1. **Create/Update Wiki Pages**
   ```powershell
   python wiki_page/rebuild_wiki.py
   ```
   This will:
   - Delete existing wiki content
   - Create a new Wiki Space
   - Create all disease pages
   - Set up proper navigation structure

2. **Restructure Content**
   ```powershell
   python wiki_page/restructure_content.py
   ```
   This will:
   - Standardize all disease page content
   - Create backups of original content
   - Ensure consistent formatting

### Patient Management

1. **Import Patient Data**
   ```powershell
   python patient_management/create_patients.py
   ```

## Content Structure

Each disease page follows this structure:
```markdown
# Disease Name

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
```

## Development Guidelines

1. Always create backups before making bulk changes
2. Test changes on a few pages before running on the entire dataset
3. Use the provided scripts for content management
4. Follow the standardized content structure
5. Keep sensitive information in `.env` file

## Error Handling

- Scripts include retry mechanisms for API calls
- Backups are automatically created
- Detailed error logging
- Graceful failure handling

## Contributing

1. Create a new branch for your feature
2. Follow the existing code structure
3. Update documentation as needed
4. Submit a pull request

## Security

- Never commit `.env` file
- Keep API keys secure
- Use environment variables for sensitive data
- Follow ERPNext security best practices

## Support

For issues or questions:
1. Check existing documentation
2. Contact RDSS administrators
3. Review ERPNext documentation

## License

Copyright © 2025 Rare Disease Support Singapore (RDSS). All rights reserved.
