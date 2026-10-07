# Zamp AI - Take-Home Case Study
**Candidate:** Saksham Gupta
**Role:** AI Solutions Analyst (Apprentice/Intern)

## The Problem
Processing unstructured invoices is a massive operational bottleneck. Companies receive invoices in various formats (PDFs, emails, docs), and human analysts spend hours manually matching the invoiced amount to the original Purchase Order (PO) in their database. 

## The Solution (Workflow)
This prototype automates the end-to-end reconciliation process:
1. **Extraction:** An LLM (`gemini-1.5-flash`) reads unstructured invoice text and extracts structured JSON (`vendor_name`, `po_number`, `total_amount`).
2. **Reconciliation:** The system queries a mock SQLite/JSON database for the matching PO.
3. **Business Logic:** It applies a strict 5% tolerance rule. If the invoice amount matches the PO amount (within 5%), it is auto-approved. If it exceeds 5%, it flags for "HUMAN REVIEW". If the PO doesn't exist, it is "REJECTED".

## How to Run
1. Ensure you have Python installed.
2. Install dependencies: `pip install google-generativeai`
3. Export your Gemini API key: `export GEMINI_API_KEY="your_api_key_here"`
4. Run the engine: `python3 main.py`

## Edge Cases Handled by Design
- **Fuzzy extraction:** The LLM successfully ignores extra text (like "Late Fee Penalty" or "Travel Expenses") and strips currency symbols (`$`) and commas automatically.
- **Tolerance thresholds:** Business operations rarely match to the exact penny due to taxes/shipping. A 5% tolerance handles this gracefully without requiring human intervention for minor variances.
- **Missing POs:** Hard-rejects invoices that attempt to reference non-existent POs, preventing fraud.
