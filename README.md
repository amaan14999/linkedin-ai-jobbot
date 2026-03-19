# LinkedIn AI JobBot
![linkedin-ai-jobbot](https://socialify.git.ci/amaan14999/linkedin-ai-jobbot/image?language=1&name=1&owner=1&pattern=Solid&theme=Dark)

An automated daemon that scrapes LinkedIn for targeted job postings, filters out previously seen roles, analyzes the job descriptions against your resume using Google's Gemini AI, and logs high-matching opportunities directly into a Google Sheet.

## Prerequisites

- Python 3.9 or higher
- A Google Cloud Platform account
- A Google Gemini API Key

---

## Structure Overview

```
linkedin-ai-jobbot/
├─ Dockerfile                 # Instructions to build your container
├─ docker-compose.yml         # Manages the container and local volumes (for SQLite)
├─ requirements.txt           # Python dependencies
├─ config.yaml                # Search keywords, locations, etc.
├─ prompts.txt                # Your exact instructions for Gemini
├─ .env.sample                # SECRETS (Gemini API Key, Google Sheet ID) - DO NOT COMMIT
├─ google_credentials.json    # Sheets service account JSON - DO NOT COMMIT
├─ README.md
│
└─ jobbot/
   ├─ main.py                 # The Daemon Entrypoint (Scheduler)
   ├─ config.py               # Parses config.yaml
   ├─ models.py               # Dataclasses (Job)
   ├─ linkedin_client.py      # The web scraper
   ├─ db.py                   # SQLite database for deduplication
   ├─ gemini_client.py        # AI scoring and resume feedback
   ├─ sheets_client.py        # Pushes new jobs to Google Sheets
   ├─ pdf_parser.py           # Parses PDF resumes
   └─ pipeline.py             # The orchestrator tying it all together
```

## Step 1: Local Setup & Virtual Environment

1. Clone this repository to your local machine.
2. Open your terminal and navigate to the root directory of the project.
3. Create a Python virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`

   - Mac/Linux: `source venv/bin/activate`

5. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Step 2: API Keys & Credentials

**A. Google Gemini API**

1. Go to **[Google AI Studio](https://aistudio.google.com/)** and generate a new API Key.
2. Copy this key; you will need it for the `.env` file.

**B. Google Sheets API (Service Account)**

1. Go to the **[Google Cloud Console](https://console.cloud.google.com/)**.
2. Create a new project or select an existing one.
3. Navigate to **[APIs & Services](https://console.cloud.google.com/apis/dashboard) > Library** and enable both the **Google Sheets API** and **Google Drive API**.
4. Go to **[APIs & Services](https://console.cloud.google.com/apis/dashboard) > Credentials**.

5. Click **Create Credentials > Service Account**. Name it **jobbot** and create it.

6. Click on your newly created Service Account, navigate to the **Keys** tab, and click **Add Key > Create New Key (JSON)**.
7. Download the JSON file, rename it exactly to `google_credentials.json`, and place it in the root directory of this project.

**C. Creating and Linking the Google Sheet**

1. Create a new, blank Google Sheet.

2. Open your `google_credentials.json` file and copy the `client_email` address.

3. In your Google Sheet, click **Share** and add that specific email address as an **Editor**. _(Crucial: The bot cannot write to the sheet without this step)_.
4. Extract your Sheet ID from the URL. If your URL is `https://docs.google.com/spreadsheets/d/1abc123XYZ/edit`, your ID is `1abc123XYZ`.

**D. The `.env` File**

1. Locate the `.env.sample` file in the root directory and rename it to `.env`.
2. Populate it with your keys:

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GOOGLE_SHEET_ID=your_google_sheet_id_here
   ```

## Step 3: Personalization and Configuration

1. **Add Your Resume:** Place your resume in the root directory of the project as a PDF file (e.g., `resume.pdf`).
2. **Configure the Bot:** Open `config.yaml` and update the search parameters.
   - Update the `resume_file` property under the `app` section to match the exact filename of your PDF.
   - Adjust your target keywords, location, experience levels, and blocked companies in the `linkedin` section.
   - Adjust your minimum AI score threshold and API rate limits.

## Step 4: Running the Bot Locally

To start the bot, ensure your virtual environment is active and run the main module from the root directory:

```bash
python -m jobbot.main
```

The bot will perform an initial fetch, process the jobs, configure your Google Sheet headers automatically, and then go to sleep, waking up hourly to check for new roles.
