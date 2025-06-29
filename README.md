# AI-Powered Eligibility Verification Bot

This project is an automated Robotic Process Automation (RPA) bot designed to streamline the insurance eligibility and verification (E&V) process for healthcare providers. It uses Google's Gemini AI to intelligently navigate web portals, fill forms, and parse reports, making it highly adaptable to different payer websites.

[Project Link](https://github.com/saqibcodes007/EligibilityBot)

## Table of Contents

- [Features](#features)
- [Workflow](#workflow)
- [Demo](#demo)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgements](#acknowledgements)

## Features

* **Continuous Operation:** Runs 24/7, checking for new patient records in a Google Sheet at set intervals.
* **Automated Web Navigation:** Securely logs into the Trizetto portal, handling OTP authentication where required.
* **AI-Powered Payer Selection:** Intelligently identifies and selects the correct payer from a complex, categorized list, even with name variations (e.g., matching "BCBS" to "Blue Cross Blue Shield" or "UMR" to "UMR-Wausau").
* **AI-Powered Form Filling:** Dynamically analyzes payer-specific eligibility forms to identify and fill the correct fields for Date of Service (DOS), Member ID, Name, and Date of Birth (DOB), ignoring unnecessary fields like dropdowns.
* **AI-Powered Report Parsing:** Reads and understands the final eligibility report HTML to accurately extract the policy status, plan start date, and plan end date, regardless of the report's layout.
* **Automated Reporting:** Updates the Google Sheet with the results, including a direct link to a screenshot of the report uploaded to Google Drive for auditing purposes.
* **Error Handling & State Management:** Manages login sessions, retries on API errors, handles on-page form validation errors, and logs all actions and issues clearly for review.

## Workflow

The bot follows a continuous loop with the following steps:

1.  **Read Google Sheet:** Checks the designated spreadsheet for a new row where the initial patient data columns are filled, but the `Status` column is empty.
2.  **Mark as Processing:** Immediately updates the `Status` column to "Processing..." to prevent duplicate work.
3.  **Launch & Log In:** Launches a headless web browser and logs into the Trizetto portal, using a saved session state if available.
4.  **AI Payer Selection:** Navigates to the eligibility page and uses Gemini AI to analyze the payer list and select the correct payer based on the name in the spreadsheet.
5.  **AI Form Filling:** Once the payer-specific form loads, the AI analyzes the form's HTML and generates a plan to fill in the patient's data into the correct fields.
6.  **Submit & Parse:** The bot executes the AI's plan, submits the form, and waits for the eligibility report. It then sends the report's HTML to the AI for parsing.
7.  **Record Results:** The AI returns the patient's `Status`, `Policy Begin`, and `Policy End` dates.
8.  **Screenshot & Upload:** The bot takes a screenshot of the report, uploads it to a shared Google Drive folder, and gets a shareable link.
9.  **Update Sheet:** The bot writes the Status, Policy Begin, Policy End, and the Google Drive screenshot link back to the corresponding row in the Google Sheet.
10. **Loop:** The process repeats, continuously checking for the next unprocessed row.

## Demo

Click the image below to watch a full video demonstration of the bot in action.

[![Bot Demo Video](https://raw.githubusercontent.com/your-username/your-repo-name/main/path/to/your/thumbnail.png)](https://drive.google.com/file/d/1HIW8NH1vpYvuf_N2qPPW-GvoENqRtiNC/view?usp=sharing)

## Tech Stack

* **Language:** Python 3
* **Web Automation:** Playwright
* **AI / LLM:** Google Gemini API (`gemini-2.0-flash-lite`)
* **Data Source & Reporting:** Google Sheets API
* **File Storage:** Google Drive API

## Installation

These instructions are tailored for a Linux environment like Google Cloud Shell.

#### **Prerequisites**

* A Google Cloud Platform project with the Google Sheets API and Google Drive API enabled.
* A Google Service Account with "Editor" access to both the target Google Sheet and the Google Drive folder.
* The `credentials.json` file for the Service Account.
* An API key for the Gemini AI from Google AI Studio.

#### **Installation Steps**

1.  **Create Project Directory:**
    ```bash
    mkdir -p eligibility_bot
    cd eligibility_bot
    ```

2.  **Add Credentials File:**
    Upload your `credentials.json` file into this directory.

3.  **Create the Python Script:**
    Create a file named `bot.py` inside this directory and paste the latest version of the bot's code into it.

4.  **Create `requirements.txt`:**
    Create a file named `requirements.txt` with the following content:
    ```
    playwright
    gspread
    google-auth-oauthlib
    google-api-python-client
    google-generativeai
    ```

5.  **Install Dependencies:**
    Run the following commands to install the required Python packages and the necessary web browsers for Playwright.
    ```bash
    pip3 install -r requirements.txt
    playwright install
    ```

## Configuration

Before running the bot, you must configure the constants at the top of the `bot.py` script:

* `GEMINI_API_KEY`: Paste your API key from Google AI Studio.
* `TRIZETTO_USERNAME`: Your Trizetto portal username.
* `TRIZETTO_PASSWORD`: Your Trizetto portal password.
* `OTP_EMAIL_ADDRESS_TEXT`: The exact text of the email option on the Trizetto OTP page (e.g., "em***@example.com").
* `SPREADSHEET_ID`: The ID of your Google Sheet.
* `DRIVE_FOLDER_ID`: The ID of the Google Drive folder where screenshots will be saved.

## Usage

1.  **Navigate to the project directory:**
    ```bash
    cd /path/to/your/eligibility_bot
    ```

2.  **Run the script in the background:**
    It is recommended to use a terminal multiplexer like `screen` or `tmux` to keep the script running even after you disconnect from the shell.
    ```bash
    # Start a new screen session
    screen -S eligibility_bot_session

    # Run the script
    python3 bot.py

    # Detach from the screen session by pressing Ctrl+A then D
    # You can re-attach later with: screen -r eligibility_bot_session
    ```

3.  **Add Data to Google Sheet:**
    While the bot is running, add new patient information to a new row in the configured Google Sheet. The bot will automatically detect and process it on its next cycle.

## Future Enhancements

* **Expand Payer Support:** Adapt the bot to handle non-commercial payers (e.g., Medicare, Medicaid) by enhancing the AI payer selection prompt.
* **Advanced Benefit Extraction:** Upgrade the AI report-parsing prompt to extract more complex benefit details, such as co-pay amounts, deductibles, and out-of-pocket maximums.
* **Multi-Client & Multi-Portal Capability:** Develop a framework to allow the bot to select different client SOPs and log in to various EDI portals (like Availity or Waystar) based on the input data.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss proposed changes.

## License

This project is licensed under the MIT License - see the `LICENSE.md` file for details.

## Contact

**SAQIB SHERWANI** 

[My GitHub](https://github.com/saqibcodes007)

[Email Me!](sherwanisaqib@gmail.com)

## Acknowledgements

* RCM and Eligibility Verification Team at Panacea Smart Solutions for their domain expertise.
* The developers of Playwright and the Google AI team.

---
<p align="center">
  Developed by Saqib Sherwani
  <br>
  Copyright © 2025 • All Rights Reserved
</p>
