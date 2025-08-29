# Al Rawdha Mosque Matrimonial Services Automation

This project helps automate Al Rawdha Mosque's matrimonial services. Here's how it works:

1. **Data Collection**: Individuals input their information via a Google Form
2. **Storage**: Form responses are stored in a Google Sheet (referred to as the **raw sheet**)
3. **Processing**: Information is processed and added to a **processed sheet** (`proc_sheet`)
4. **PDF Generation**: The information is converted into a PDF format
5. **Email Distribution**: The PDF is emailed to the individual, ready to be posted on the Al Rawdha WhatsApp broadcasting service

This code is designed to be generalisable for any other community that wishes to set up a similar matrimonial service.

---

## Setup

### 1. Pull the repository
```bash
git clone <git@github.com:imy99/alrawdha_match.gitl>
```

### 2. Create conda environment
```bash
make env
```

### 3. Activate environment
```bash
conda activate alrawdha_match
```

### 4. Set up credentials

#### `.env` file
```make credentials
```
- Create a `.env` file in the root directory
- Include credentials from the Gmail API service
- More info for this setup is provided under **Gmail API Setup** below

```env
SERVICE_ACCOUNT_FILE = "matching-service-account.json"
RAW_SHEET_NAME = # Your Form response google sheets # 
PROC_SHEET_NAME = # Initially blank google sheets to store processed data #
```

#### `matching-service-account.json` file
- This file is obtained from the Gmail API service setup
- Required for establishing the connection with Google services

### 5. Create file to run the service
```make run
```
- Process entries from the raw sheet
- Add processed data to the `proc_sheet`
- Generate PDFs
- Send emails to individuals

---

## Gmail API Setup 

### 1. Create a Google Cloud Project
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Click **Select a project** → **New Project**
- Give it a name (e.g., `AlRawdhaMatrimonial`) and click **Create**

### 2. Enable APIs
- Click **APIs & Services** → **Library**
- Search for **Gmail API** → Click **Enable**
- Search for **Google Sheets API** → Click **Enable**

### 3. Create Credentials
- Go to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**
- Configure the consent screen:
  - Choose **Internal** if only for your organization
  - Fill required fields (App name, support email, developer contact info)
- Choose **Desktop app** as the application type
- Click **Create** → **Download JSON** → Rename to `matching-service-account.json`

### 4. Generate OAuth Tokens for Gmail
Use the downloaded JSON file with a Python script or OAuth2 tool to generate:
- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- `GMAIL_REFRESH_TOKEN`

Store these values in `.env`:
```env
GMAIL_CLIENT_ID=<your-client-id>
GMAIL_CLIENT_SECRET=<your-client-secret>
GMAIL_REFRESH_TOKEN=<your-refresh-token>
```

### 5. Verify Connection
- Test access to Google Sheets and Gmail with a small Python script
- Ensure credentials allow reading/writing sheets and sending emails

---

## Usage

### Run the service
``` make run
```
This command will scan the raw sheet for any new entries that have not yet been processed.
Only these new entries are processed, transferred to the processed sheet, compiled into a PDF, and then emailed to the relevant recipients.

### Check processed sheet
Verify that entries from the raw sheet have been processed and added to `proc_sheet`.

### Send notifications (optional)
Emails can be sent to individuals using Gmail API credentials in `.env`.
