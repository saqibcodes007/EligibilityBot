# tasks.py
# Version 8: Parses the final report, extracts data, and takes a clipped screenshot.

import os
from playwright.sync_api import Page, TimeoutError

# --- Screenshot Directories ---
SUCCESS_SCREENSHOT_DIR = "/home/sherwanisaqib/Eligibility/Screenshots/Success"
ERROR_SCREENSHOT_DIR = "/home/sherwanisaqib/Eligibility/Screenshots/Error"


def run_post_login_tasks(page: Page, patient_data: dict):
    """
    Receives the logged-in page object and performs the desired tasks.
    :param page: The Playwright page object from the main bot.
    :param patient_data: A dictionary containing all patient and payer info.
    """
    print("\n--- Control handed over to Task Handler ---")
    try:
        # --- Navigation and Form Filling ---
        print("1. Navigating to the Individual Inquiry form...")
        page.locator("#NavCtrl_navManagePatients").hover()
        page.locator("#NavCtrl_hlEligibility").click()
        page.wait_for_url("**/ManagePatients/default.aspx?id=PatientEligibility", timeout=30000)
        page.get_by_role("link", name="Run Individual Eligibility Inquiry").click()
        page.wait_for_url("**/ManagePatients/RealTimeEligibility/Index**", timeout=30000)
        print("2. Selecting payer and filling form...")
        page.locator('a.payer-category:has-text("Commercial")').click()
        commercial_list_container = page.locator("li#Commercial ul.insurersDetail")
        payer_element = commercial_list_container.get_by_text(patient_data['payer_name'], exact=True)
        payer_element.wait_for(timeout=10000)
        payer_element.click()
        page.wait_for_timeout(2000)
        
        # Fill Form
        page.locator("#EligibilityRequestPayerInquiry_EligibilityRequestFieldValues_DateOfService").fill(patient_data["dos"])
        page.locator("#EligibilityRequestPayerInquiry_EligibilityRequestFieldValues_DateOfServiceEnd").fill(patient_data["dos"])
        page.locator("#EligibilityRequestTemplateInquiry_EligibilityRequestFieldValues_InsuranceNum").fill(patient_data["member_id"])
        page.locator("#EligibilityRequestTemplateInquiry_EligibilityRequestFieldValues_InsuredFirstName").fill(patient_data["first_name"])
        page.locator("#EligibilityRequestTemplateInquiry_EligibilityRequestFieldValues_InsuredLastName").fill(patient_data["last_name"])
        page.locator("#EligibilityRequestTemplateInquiry_EligibilityRequestFieldValues_InsuredDob").fill(patient_data["dob"])
        print("   Form filled.")

        # --- Submit and Parse Report ---
        print("3. Submitting the eligibility inquiry...")
        page.locator("#btnUploadButton").click()
        
        print("\n--- Inquiry Submitted. Waiting for and parsing report... ---")

        # Wait for a unique element on the report page to ensure it has loaded
        status_element = page.locator("#trnEligibilityStatus")
        status_element.wait_for(timeout=30000)

        # Extract the required information using locators from the report HTML
        eligibility_status = status_element.text_content().strip()
        plan_begin_date = page.locator('dt:has-text("Plan Begin Date:") + dd').text_content().strip()
        plan_end_date = page.locator('dt:has-text("Plan End Date:") + dd').text_content().strip()

        report_data = {
            "Eligibility Status": eligibility_status,
            "Plan Begin Date": plan_begin_date,
            "Plan End Date": plan_end_date,
        }

        # --- Take Screenshot and Display Results ---
        os.makedirs(SUCCESS_SCREENSHOT_DIR, exist_ok=True)
        screenshot_path = os.path.join(SUCCESS_SCREENSHOT_DIR, "SUCCESS_eligibility_report.png")
        
        # Locate the specific report container to screenshot the top part of the page
        report_container = page.locator("#eligibilityRequestResponse")
        report_container.screenshot(path=screenshot_path)
        print(f"\nReport screenshot saved to '{screenshot_path}'.")

        # Print the final extracted data in an organized format
        print("\n--- Eligibility Report Summary ---")
        for key, value in report_data.items():
            print(f"   - {key}: {value}")
        print("---------------------------------")

    except Exception as e:
        print(f"\n--- AN ERROR OCCURRED IN THE TASK HANDLER ---")
        print(f"Error: {e}")
        if not page.is_closed():
            os.makedirs(ERROR_SCREENSHOT_DIR, exist_ok=True)
            screenshot_path = os.path.join(ERROR_SCREENSHOT_DIR, "error_screenshot_tasks.png")
            page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to '{screenshot_path}'")
