import os
import csv
import json
from datetime import datetime
import requests
from dotenv import load_dotenv
import pandas as pd
import uuid
import anthropic

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Load environment variables from parent directory
load_dotenv(os.path.join(parent_dir, '.env'))

# ERPNext credentials
api_key = os.getenv('ERPNEXT_RDSS_API_KEY')
api_secret = os.getenv('ERPNEXT_RDSS_API_SECRET')
erpnext_url = os.getenv('ERPNEXT_RDSS_URL')

# Anthropic API setup
anthropic_client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

def extract_patient_info_with_claude(content):
    """Use Claude-3 to extract patient information from story content"""
    try:
        message = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            temperature=0,
            system="You are a medical data extraction assistant. Extract key patient information from the given text and return it in JSON format. Focus on: gender, date of birth (if mentioned), blood group (if mentioned), medical conditions, and any contact information.",
            messages=[{
                "role": "user",
                "content": f"Extract patient information from this text and return ONLY a JSON object with these fields: gender (Male/Female), dob (YYYY-MM-DD or empty), blood_group (A+/A-/B+/B-/O+/O-/AB+/AB- or empty), medical_conditions (array of strings), contact_info (object with email and phone if present). Text: {content}"
            }]
        )
        
        try:
            # Extract JSON from Claude's response
            response_text = message.content[0].text
            # Find JSON block in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Error parsing Claude response: {str(e)}")
            return {}
            
    except Exception as e:
        print(f"Error calling Claude API: {str(e)}")
        return {}

def get_diagnosis_from_title(title):
    """Extract diagnosis from the title field"""
    if isinstance(title, str) and 'Diagnosis:' in title:
        return title.split('Diagnosis:')[1].strip()
    return ''

def format_phone_number(phone):
    """Format and validate phone number"""
    if not phone or phone.lower() in ['unknown', 'empty']:
        return ''
    # Remove any non-digit characters
    digits = ''.join(filter(str.isdigit, str(phone)))
    if len(digits) >= 8:  # Basic validation for Singapore numbers
        return digits
    return ''

def format_blood_group(blood_group):
    """Convert blood group to valid format"""
    valid_groups = {
        'A+': 'A Positive', 'A-': 'A Negative',
        'B+': 'B Positive', 'B-': 'B Negative',
        'O+': 'O Positive', 'O-': 'O Negative',
        'AB+': 'AB Positive', 'AB-': 'AB Negative'
    }
    if not blood_group:
        return ''
    return valid_groups.get(blood_group, '')

def format_medical_history(conditions):
    """Convert medical conditions list to string format"""
    if not conditions:
        return ''
    # Filter out empty/None values and join with semicolons
    valid_conditions = [str(c) for c in conditions if c]
    return '; '.join(valid_conditions)

def format_email(email):
    """Format and validate email address"""
    if not email or email.lower() in ['unknown', 'empty']:
        return None  # Return None instead of empty string to skip the field entirely
    if '@' in email and '.' in email:  # Basic email validation
        return email.strip()
    return None

def check_patient_exists(patient_name, headers):
    """Check if patient already exists in ERPNext"""
    try:
        # Encode the patient name for URL
        encoded_name = requests.utils.quote(patient_name)
        response = requests.get(
            f'{erpnext_url}/api/resource/Patient?filters={{"patient_name":"{encoded_name}"}}',
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            return len(data.get('data', [])) > 0
        return False
    except Exception as e:
        print(f"Error checking patient existence: {str(e)}")
        return False

def transform_patient_data(stories_file, patient_template_file):
    try:
        # Read the stories CSV file with explicit encoding
        stories_df = pd.read_csv(stories_file, encoding='utf-8-sig')
        
        # Read the Patient template CSV to understand the required format
        patient_template_df = pd.read_csv(patient_template_file, encoding='utf-8-sig')
        
        print(f"Stories columns: {stories_df.columns.tolist()}")
        print(f"Patient template columns: {patient_template_df.columns.tolist()}")
        
        # Create a new DataFrame with the required Patient.csv columns
        patients = []
        
        for _, row in stories_df.iterrows():
            try:
                # Extract patient name from post_title
                full_name = str(row['post_title']).strip()
                
                # Skip if no name
                if not full_name or full_name.lower() == 'nan':
                    continue
                
                # Split name into parts (assuming single name if can't split)
                name_parts = full_name.split()
                first_name = name_parts[0] if name_parts else full_name
                last_name = name_parts[-1] if len(name_parts) > 1 else ''
                middle_name = ' '.join(name_parts[1:-1]) if len(name_parts) > 2 else ''
                
                # Get diagnosis from post_excerpt
                diagnosis = get_diagnosis_from_title(str(row['post_excerpt']))
                
                # Use Claude to extract additional information from post_content
                content_info = extract_patient_info_with_claude(str(row['post_content']))
                
                # Generate a unique ID for the patient
                patient_id = str(uuid.uuid4())[:8].upper()
                
                # Create patient record with required fields
                patient = {
                    'doctype': 'Patient',
                    'first_name': first_name,
                    'middle_name': middle_name,
                    'last_name': last_name,
                    'patient_name': full_name,  # This is the display name
                    'sex': content_info.get('gender', 'Female'),  # Default to Female if not found
                    'blood_group': format_blood_group(content_info.get('blood_group', '')),  # Empty if invalid
                    'dob': content_info.get('dob', ''),
                    'status': 'Active',
                    'mobile': format_phone_number(content_info.get('contact_info', {}).get('phone', '')),
                    'email': format_email(content_info.get('contact_info', {}).get('email', '')),
                    'patient_id': f'PAT-{patient_id}',  # Required unique identifier
                    'medical_history': format_medical_history(
                        ([diagnosis] if diagnosis else []) + content_info.get('medical_conditions', [])
                    )
                }
                
                # Remove None values from the patient dict
                patient = {k: v for k, v in patient.items() if v is not None}

                patients.append(patient)
                print(f"Processed patient: {full_name}")
                
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        return patients
    except Exception as e:
        print(f"Error reading CSV files: {str(e)}")
        raise

def create_patient_in_erpnext(patient_data):
    """Create a patient record in ERPNext using the API"""
    headers = {
        'Authorization': f'token {api_key}:{api_secret}',
        'Content-Type': 'application/json',
    }
    
    try:
        # Check if patient already exists
        if check_patient_exists(patient_data['patient_name'], headers):
            print(f"Patient already exists: {patient_data['patient_name']}")
            return True  # Consider this a success case
            
        # Remove email field if it's None
        if 'email' in patient_data and patient_data['email'] is None:
            del patient_data['email']
            
        response = requests.post(
            f'{erpnext_url}/api/resource/Patient',
            headers=headers,
            json=patient_data
        )
        
        if response.status_code == 409:  # Conflict - patient already exists
            print(f"Patient already exists (409): {patient_data['patient_name']}")
            return True
            
        response.raise_for_status()
        print(f"Successfully created patient: {patient_data['patient_name']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating patient {patient_data['patient_name']}: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False

def main():
    # File paths
    stories_file = os.path.join(current_dir, 'stories_bene_export_rdss_site.csv')
    patient_template_file = os.path.join(current_dir, 'Patient.csv')
    
    print("Starting patient data transformation...")
    print(f"Stories file: {stories_file}")
    print(f"Patient template file: {patient_template_file}")
    
    # Transform the data
    patients = transform_patient_data(stories_file, patient_template_file)
    
    if not patients:
        print("No valid patients found to import")
        return
    
    print(f"\nFound {len(patients)} patients to import")
    
    # Create patients in ERPNext
    successful = 0
    failed = 0
    
    for patient in patients:
        result = create_patient_in_erpnext(patient)
        if result:
            successful += 1
        else:
            failed += 1
    
    print(f"\nSummary:")
    print(f"Successfully created: {successful} patients")
    print(f"Failed to create: {failed} patients")

if __name__ == '__main__':
    main()