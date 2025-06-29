# bot.py
# Version 5.3 - Final Corrected Version with Robust AI Payer Selection and Error Handling.

import os
import time
import json
from playwright.sync_api import sync_playwright, Page, TimeoutError
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- CONFIGURATION ---

# IMPORTANT: PASTE YOUR GEMINI API KEY HERE
GEMINI_API_KEY = "Gemini API Key"

# Trizetto Credentials
TRIZETTO_USERNAME = "username"
TRIZETTO_PASSWORD = "password"
OTP_EMAIL_ADDRESS_TEXT = "email@email.com" # IMPORTANT: Update with the real email text

# Google Services Configuration
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SPREADSHEET_ID = 'spreadsheet ID'
SHEET_NAME = 'Sheet1'
DRIVE_FOLDER_ID = 'folder ID' 
CHECK_INTERVAL_SECONDS = 60

# --- File/Path Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(SCRIPT_DIR, 'credentials.json')
STATE_FILE = os.path.join(SCRIPT_DIR, "login_state.json")
SCREENSHOT_DIR = os.path.join(SCRIPT_DIR, "Screenshots")

# --- AI AND AUTOMATION LOGIC ---

def upload_screenshot_to_drive(drive_service, folder_id, file_path):
    """Uploads a file to Google Drive and returns its shareable link."""
    try:
        print(f"   - Uploading '{os.path.basename(file_path)}' to Google Drive...")
        file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
        media = MediaFileUpload(file_path, mimetype='image/png', resumable=True)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        file_id = file.get('id')
        drive_service.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()
        print("   - Upload successful.")
        return file.get('webViewLink')
    except Exception as e:
        print(f"   -!- Google Drive upload failed: {e}")
        return "Drive Upload Failed"

def generate_form_fill_plan(page_html: str, patient_data: dict) -> list:
    """Uses Gemini to generate a plan to fill the web form."""
    print("   - Asking AI to generate a form-filling plan...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    prompt = f"""
    You are a meticulous web automation assistant. Your task is to analyze the provided HTML of a web form and a JSON object of patient data. Create a JSON array of steps to fill ALL necessary fields based on the patient data provided.

    **CRITICAL INSTRUCTIONS:**
    1.  **Identify All Required Fields:** You MUST find and create steps for the input fields associated with the following labels: Date of Service (and Date of Service End, if present), Subscriber ID (or Member ID), Subscriber First Name (or First Name), Subscriber Last Name (or Last Name), and Subscriber Date of Birth (or DOB).
    2.  **Map Data:** Use the provided patient data to map values to the fields you identified. If you find both "Date of Service" and "Date of Service End", use the `dos` value for both.
    3.  **Generate Robust CSS Selectors:** Create a precise CSS selector for each input field. Prefer using element IDs.
    4.  **Ignore Dropdowns:** Your plan must ONLY include actions for text `<input>` elements. Do NOT generate steps for `<select>` elements like "Search By".
    5.  **Return a JSON Array ONLY:** The output must be a valid JSON array of objects. Each object must have a "selector" key and a "value" key.

    **Patient Data:**
    ```json
    {json.dumps(patient_data, indent=2)}
    ```

    **Form HTML:**
    ```html
    {page_html}
    ```
    """
    try:
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        plan = json.loads(cleaned_text)
        print("   - AI form-fill plan generated successfully.")
        return plan
    except Exception as e:
        print(f"   -!- CRITICAL: AI failed to generate a valid form-fill plan: {e}")
        raw_text = "unavailable"
        if 'response' in locals() and hasattr(response, 'text'):
            raw_text = response.text
        print(f"   -!- Raw AI response was: {raw_text}")
        return []

def parse_report_with_ai(html_content: str) -> dict:
    """Uses the Gemini AI to parse the HTML of an eligibility report."""
    print("   - Asking AI to parse the report with enhanced logic...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    prompt = f"""
    You are an expert data extraction bot. Analyze the HTML of an insurance report.
    Find "Eligibility Status", "Plan Begin Date", and "Plan End Date".
    CRITICAL: The report may have multiple "Plan Begin" dates for sub-benefits (like Vision, Dental). You MUST identify the date associated with the main "Health Benefit Plan Coverage" or the primary policy.
    If a date is a range like "1/1/2025 - 12/31/2025", extract both.
    If not found, return "Not Found".
    Return ONLY a valid JSON object with keys: "status", "policy_begin", "policy_end".
    HTML:
    ```html
    {html_content}
    ```
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result_json = json.loads(cleaned_response_text)
        print("   - AI successfully parsed data.")
        return result_json
    except Exception as e:
        raw_text = "unavailable"
        if 'response' in locals() and hasattr(response, 'text'):
            raw_text = response.text
        print(f"   -!- AI parsing failed: {e}. Raw response: {raw_text}")
        return {"status": "AI Error", "policy_begin": "AI Error", "policy_end": str(e)}

def select_payer_with_ai(page: Page, payer_name: str):
    """Uses Gemini AI to find and select the correct payer from a complex list."""
    print("   - Starting AI-powered payer selection...")
    page.goto("https://mytools.gatewayedi.com/ManagePatients/RealTimeEligibility/Index", wait_until="domcontentloaded")
    
    payer_list_container = page.locator("#InsurerAccordion")
    payer_list_container.wait_for(state="visible", timeout=30000)
    list_html = payer_list_container.inner_html()
    
    print("   - Asking AI to find the best payer match and create a plan...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    prompt = f"""
    You are an expert web automation assistant. Analyze the provided HTML of a payer list and a target payer name. Generate a two-step JSON plan to select the correct payer.
    1.  The user wants to select: **"{payer_name}"**.
    2.  Find the Best Match: Determine which category the target payer belongs to. Then, find the best and most logical match for the target name within that category's list. For example, if the target is "UMR", match it to "UMR-Wausau". If the target is "BCBS North Carolina", find the "Blue Cross Blue Shield" category and then the "BCBS North Carolina" link.
    3.  Return ONLY a JSON object with two keys: "category_text" (the exact text of the category link) and "payer_text" (the exact text of the final payer link).
    **Payer List HTML:**
    ```html
    {list_html}
    ```
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        plan = json.loads(cleaned_text)

        print(f"   - AI Plan Received. Category: '{plan['category_text']}', Payer: '{plan['payer_text']}'")
        
        print("   - Clicking category...")
        # FIX: Use get_by_text which is robust for elements without hrefs.
        category_element = page.get_by_text(plan['category_text'], exact=True).first
        category_element.click()
        page.wait_for_timeout(1000)
        
        print("   - Clicking final payer...")
        # FIX: Find the correct container for the payer links after the category is clicked.
        payer_list_container = page.locator(f"li[id='{plan['category_text']}'] ul.insurersDetail")
        payer_link = payer_list_container.get_by_text(plan['payer_text'], exact=True).first
        payer_link.click()
        
        page.wait_for_timeout(2000)
        print(f"   - AI Payer Selection for '{payer_name}' successful.")

    except Exception as e:
        print(f"   -!- CRITICAL: AI-driven payer selection failed: {e}")
        raise e

def process_patient(page: Page, drive_service, patient_data: dict) -> dict:
    """Handles the AI-driven form filling, result parsing, and screenshot upload for a patient."""
    screenshot_link = "N/A"
    try:
        form_html = page.locator("body").inner_html()
        
        fill_plan = generate_form_fill_plan(form_html, patient_data)
        if not fill_plan:
            raise ValueError("AI did not return a valid form-filling plan.")

        print("   - Executing AI form-filling plan...")
        for step in fill_plan:
            print(f"     - Filling selector '{step['selector']}' with value '{step['value']}'")
            page.locator(step['selector']).fill(step['value'])
        print("   - Form filled according to AI plan.")

        page.locator("#btnUploadButton").click()
        
        print("   - Waiting for response (success or error)...")
        page.wait_for_selector(
            "#eligibilityRequestResponse, #EligibilityValidationErrors",
            timeout=45000
        )

        error_div = page.locator("#EligibilityValidationErrors")
        if error_div.is_visible() and len(error_div.inner_text().strip()) > 0:
            raise ValueError(f"Form submission error on page: {error_div.inner_text().strip()}")

        report_container = page.locator("#eligibilityRequestResponse")
        report_html = report_container.inner_html()
        report_data = parse_report_with_ai(report_html)

        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"SUCCESS_{patient_data['last_name']}_{patient_data['first_name']}.png")
        report_container.screenshot(path=screenshot_path)
        
        screenshot_link = upload_screenshot_to_drive(drive_service, DRIVE_FOLDER_ID, screenshot_path)
        report_data['screenshot_link'] = screenshot_link

        print(f"-> Check complete for {patient_data['first_name']}. Status: {report_data.get('status')}")
        return report_data

    except Exception as e:
        print(f"   -!- An error occurred during patient processing: {e}")
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"ERROR_{patient_data['last_name']}_{patient_data['first_name']}.png")
        page.screenshot(path=screenshot_path)
        
        screenshot_link = upload_screenshot_to_drive(drive_service, DRIVE_FOLDER_ID, screenshot_path)
        
        return {"status": f"Error: {type(e).__name__}", "policy_begin": f"{e}", "policy_end": "", "screenshot_link": screenshot_link}

# --- MAIN BOT LOOP ---

def main():
    """Main function to run the bot loop."""
    print("--- Eligibility Bot (AI Full Suite v5.3) Starting Up ---")
    if not GEMINI_API_KEY or "YOUR_GEMINI_API_KEY_HERE" in GEMINI_API_KEY:
        print("\n!!! FATAL ERROR: Please paste your Gemini API key and restart.")
        return

    print("-> Authenticating with Google Services...")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    sheets_client = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)
    sheet = sheets_client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    print("-> Google Sheets & Drive authentication successful.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=50)
        context, page = (None, None)
        
        if os.path.exists(STATE_FILE):
            try:
                print("-> Found saved session. Attempting to use...")
                context = browser.new_context(storage_state=STATE_FILE)
                page = context.new_page()
                page.goto("https://mytools.gatewayedi.com/default.aspx", timeout=60000)
                page.locator("#NavCtrl_navHome").wait_for(timeout=15000)
                print("-> Session is valid. Login skipped.")
            except Exception as e:
                print(f"-> Session invalid: {e}. A new login is required.")
                if context: context.close()
                context = None
        
        if not context:
            print("-> Performing new login to Trizetto...")
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://mytools.gatewayedi.com/LogOn")
            page.fill('input[name="UserName"]', TRIZETTO_USERNAME)
            page.fill('input[type="password"]', TRIZETTO_PASSWORD)
            page.click('input[type="submit"]')
            print("   - Handling OTP step...")
            page.locator(f'text={OTP_EMAIL_ADDRESS_TEXT}').click()
            otp_code = input(">>> Please check your email for the OTP and enter it here: ")
            page.locator("#AuthCode").press_sequentially(otp_code, delay=100)
            page.locator("#btnVerify").click()
            page.wait_for_url("**/default.aspx**", timeout=30000)
            print("-> LOGIN SUCCESSFUL! Saving session...")
            context.storage_state(path=STATE_FILE)

        while True:
            try:
                print(f"\n--- Checking for new records... ({time.ctime()}) ---")
                all_rows = sheet.get_all_values()
                
                row_to_process, row_index_to_process = (None, -1)
                for i, row in enumerate(all_rows[1:], start=2):
                    if len(row) >= 6 and all(str(item).strip() for item in row[:6]) and (len(row) < 7 or not str(row[6]).strip()):
                        row_to_process, row_index_to_process = row, i
                        break

                if row_to_process:
                    current_payer = row_to_process[4].strip()
                    print(f"-> Found record in row {row_index_to_process} for Payer: '{current_payer}'")
                    
                    sheet.update_cell(row_index_to_process, 7, "Processing...")

                    select_payer_with_ai(page, current_payer)
                    
                    patient_data = {
                        "dos": row_to_process[0], "first_name": row_to_process[1],
                        "last_name": row_to_process[2], "dob": row_to_process[3],
                        "payer_name": current_payer, "member_id": row_to_process[5]
                    }

                    results = process_patient(page, drive_service, patient_data)
                    
                    print(f"-> Writing results back to row {row_index_to_process}...")
                    sheet.update_cell(row_index_to_process, 7, results.get("status", "Error"))
                    sheet.update_cell(row_index_to_process, 8, results.get("policy_begin", ""))
                    sheet.update_cell(row_index_to_process, 9, results.get("policy_end", ""))
                    sheet.update_cell(row_index_to_process, 10, results.get("screenshot_link", "Upload Failed"))
                    print("-> Sheet updated.")

                else:
                    print(f"-> No new records found. Waiting {CHECK_INTERVAL_SECONDS} seconds...")
                    time.sleep(CHECK_INTERVAL_SECONDS)

            except gspread.exceptions.APIError as e:
                print(f"-!- GOOGLE SHEETS API ERROR: {e}. Waiting 5 minutes...")
                time.sleep(300)
            except Exception as e:
                print(f"-!- AN UNEXPECTED ERROR IN THE MAIN LOOP: {e}")
                print("-!- Resetting state. Will re-navigate on next record. Waiting 60 seconds...")
                time.sleep(60)

if __name__ == "__main__":
    main()
