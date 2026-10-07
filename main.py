import os
import json
import glob
import sys
import time
from google import genai
from google.genai import errors

# Constants
TOLERANCE_PERCENTAGE = 0.05  # 5% variance allowed

def load_po_database(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)

def extract_invoice_data(invoice_text: str) -> dict:
    """Uses LLM to extract Vendor Name, PO Number, and Total Amount from unstructured text."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        print("Please run: export GEMINI_API_KEY='your_key_here'")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are a data extraction AI. Extract the following fields from the invoice text below.
    Return ONLY a raw JSON object with no markdown formatting or backticks.
    
    Fields required:
    - vendor_name (string)
    - po_number (string)
    - total_amount (float, strip all currency symbols and commas)
    
    Invoice Text:
    {invoice_text}
    """
    
    # Robust retry mechanism to handle 503 API overload on free tiers
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
            )
            break # Success, exit retry loop
        except errors.ServerError as e:
            if attempt == max_retries - 1:
                raise e
            print(f"API overloaded (503). Retrying in {2 ** attempt} seconds...")
            time.sleep(2 ** attempt)
    
    try:
        # Strip potential markdown formatting if the model disobeys
        raw_json = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_json)
        return data
    except Exception as e:
        print(f"Failed to parse LLM response: {response.text}")
        raise e

def reconcile_invoice(invoice_data: dict, po_db: dict) -> str:
    po_num = invoice_data.get('po_number')
    inv_amount = invoice_data.get('total_amount', 0.0)
    
    if po_num not in po_db:
        return f"REJECTED: PO Number '{po_num}' not found in database."
        
    po_record = po_db[po_num]
    expected_amount = po_record['expected_amount']
    
    # Calculate difference
    difference = abs(inv_amount - expected_amount)
    variance_allowed = expected_amount * TOLERANCE_PERCENTAGE
    
    if difference <= variance_allowed:
        return f"APPROVED: Amount ${inv_amount:.2f} is within 5% tolerance of expected ${expected_amount:.2f}."
    else:
        return f"REQUIRES HUMAN REVIEW: Amount ${inv_amount:.2f} exceeds 5% tolerance (Expected: ${expected_amount:.2f})."

def main():
    print("Initializing Zamp AI Workflow: Invoice Reconciliation Engine...\n")
    
    # Load Mock Database
    po_db = load_po_database('data/po_database.json')
    
    # Process all invoices in data/invoices/
    invoice_files = glob.glob('data/invoices/*.txt')
    
    for file_path in sorted(invoice_files):
        print(f"--- Processing {os.path.basename(file_path)} ---")
        with open(file_path, 'r') as f:
            invoice_text = f.read()
            
        print("Extracting data via LLM...")
        extracted_data = extract_invoice_data(invoice_text)
        print(f"Extracted: {extracted_data}")
        
        print("Reconciling against PO Database...")
        decision = reconcile_invoice(extracted_data, po_db)
        print(f"Verdict: {decision}\n")

if __name__ == "__main__":
    main()
