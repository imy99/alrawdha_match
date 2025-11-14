import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import random
from email_formation import intiation_email, error_email, ammendment_email
from pdf_formation import create_pdf
from dotenv import load_dotenv
import os
from datetime import datetime
import yaml

load_dotenv()


# Load config.yaml
with open("category_names.yaml", "r") as file:
    config = yaml.safe_load(file)

# RAW_PROFILE_GENERATOR (variables)
raw = config['2a']

# AMMENDMENT_PROFILE_GENERATOR (variables)
amm = config['2b']

# PROC_PROFILE_GENERATOR (variables)
proc = config ['3ab']


# -----------------------------
# CONFIGURATION
# -----------------------------
# Path to your service account JSON key
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

# Google Sheet name (linked to your Form responses)
RAW_PROFILE_GENERATOR = os.getenv("RAW_PROFILE_GENERATOR")
AMMENDED_PROFILE_GENERATOR  = os.getenv("AMMENDED_PROFILE_GENERATOR")
PROC_PROFILE_GENERATOR = os.getenv("PROC_PROFILE_GENERATOR")


# Gmail credentials for sending emails (can use App Password)
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # Replace with your app password

# -----------------------------
# AUTHENTICATE WITH GOOGLE SHEETS
# -----------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(creds)
raw_profile_generator = client.open(RAW_PROFILE_GENERATOR).sheet1
amm_profile_generator = client.open(AMMENDED_PROFILE_GENERATOR).sheet1
proc_profile_generator = client.open(PROC_PROFILE_GENERATOR).sheet1

print(
    "Authenticated! Read from:",
    RAW_PROFILE_GENERATOR.title(),
    "and",
    AMMENDED_PROFILE_GENERATOR.title(),
    "| Write to:",
    PROC_PROFILE_GENERATOR.title(),
)

# -----------------------------
# GET ALL RECORDS
# -----------------------------


def load_sheets(sheet):
    df = pd.DataFrame(sheet.get_all_records())
    if df.empty:
        headers = sheet.row_values(1)
        df = pd.DataFrame(columns=headers)
    return df 

raw_records = load_sheets(raw_profile_generator)  # returns a list of dicts
amm_records = load_sheets(amm_profile_generator)
proc_records = load_sheets(proc_profile_generator)


# Filter newer records
if proc_records.empty:
    new_records = raw_records.copy()


else:
    raw_records[raw["Timestamp"]] = pd.to_datetime(raw_records[raw["Timestamp"]], format='mixed', dayfirst=True)
    proc_records[proc["Timestamp"]] = pd.to_datetime(proc_records[proc["Timestamp"]], format='mixed', dayfirst=True)
    proc_records[proc["Ammended Timestamp"]] = pd.to_datetime(proc_records[proc["Ammended Timestamp"]], format='mixed', dayfirst=True)


    latest_proc_row = proc_records[[proc["Timestamp"],proc["Ammended Timestamp"]]].max()
    latest_proc_time = latest_proc_row.max()

    new_records = raw_records[raw_records["Timestamp"] > latest_proc_time].copy()
    new_records["Timestamp"] = new_records["Timestamp"].astype(str)

    if not amm_records.empty:
        amm_records[amm["Ammended Timestamp"]] = pd.to_datetime(amm_records[amm["Ammended Timestamp"]], format='mixed', dayfirst=True)
        amm_records = amm_records[amm_records[amm["Ammended Timestamp"]] > latest_proc_time].copy()

new_records.insert(1, proc["Ammended Timestamp"], "")
new_records.insert(2, proc["Profile ID"], "")
new_records.insert(3, proc["Profile Key"], "")
new_records.columns = [col.strip() for col in new_records.columns]


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------


from datetime import datetime

def process_amendments(amm_records, proc_profile_generator, proc, amm):
    """
    Process amendments directly in the Google Sheet without loading into DataFrame.

    (1) Keep existing PDF – Only update non-empty fields.
    (2) Replace PDF completely – Replace all fields except:
        proc['Profile ID'], proc['Profile Key'], proc['Timestamp'].

    Updates are written directly into the sheet.
    """

    # Load entire sheet once
    rows = proc_profile_generator.get_all_values()
    headers = rows[0]
    
    # Map header -> column index (0-based)
    col_index = {h: i for i, h in enumerate(headers)}

    # Protected columns
    protected = {
        proc["Profile ID"],
        proc["Profile Key"],
        proc["Timestamp"]
    }

    for _, amm_row in amm_records.iterrows():

        profile_id = str(amm_row.get(amm["Profile ID"], "")).strip()
        if not profile_id:
            continue

        # Find row number in sheet (skip header → start at row 1)
        row_num = None
        for i in range(1, len(rows)):
            if rows[i][col_index[proc["Profile ID"]]] == profile_id:
                row_num = i + 1   # convert to 1-indexed for gspread
                row_data = rows[i]
                break

        if row_num is None:
            print(f"⚠️ Profile ID {profile_id} not found in processed sheet.")
            continue

        style = str(amm_row.get(amm["Amendment Style"], "")).strip()

        for col_name in headers:
            if col_name in protected:
                continue

            new_value = amm_row.get(col_name, "")

            # Keep existing → only update if new data is non-empty
            if "Keep existing" in style:
                if new_value and str(new_value).strip():
                    proc_profile_generator.update_cell(
                        row_num,
                        col_index[col_name] + 1,
                        str(new_value)
                    )

            # Replace completely → always update
            elif "Replace PDF completely" in style:
                proc_profile_generator.update_cell(
                    row_num,
                    col_index[col_name] + 1,
                    str(new_value)
                )

        # Amendment timestamp update
        ammend_time_val = amm_row.get(amm["Ammended Timestamp"], "")
        if ammend_time_val and str(ammend_time_val).strip():
            proc_profile_generator.update_cell(
                row_num,
                col_index[proc["Ammended Timestamp"]] + 1,
                str(ammend_time_val)
            )

        print(f"✅ Updated Profile ID {profile_id} ({style})")


def generate_profile_key(existing_profile_key: set) -> str:
    """
    Generate a unique match authorisation code (profile_key): 5-digit code.

    existing_ids: set of already used match authorisation codes to avoid duplicates
    """

    while True:
        profile_key = f"{random.randint(0, 99999):05d}"
        if profile_key not in existing_profile_key:
            return profile_key

def generate_unique_id(gender: str, existing_ids: set) -> str:
    """
    Generate a unique Profile ID: gender + 4-digit code.

    gender: "F" or "M"
    existing_ids: set of already used IDs to avoid duplicates
    """
    if gender not in ("Female", "Male"):
        raise ValueError("Gender must be 'Female' or 'Male'")

    while True:
        code = f"{random.randint(0, 9999):04d}"
        profile_id = f"{gender[0]}{code}"
        if profile_id not in existing_ids:
            return profile_id


# -----------------------------
# MAIN WORKFLOW
# -----------------------------
if __name__ == "__main__":

    # Generating Profile ID's
    if proc_records.empty:
        existing_ids = []
        existing_profile_key = []
    else:
        existing_ids = proc_records[proc["Profile ID"]].to_list()
        existing_profile_key = proc_records[proc["Profile Key"]].to_list()


    for i, row in new_records.iterrows():
        new_id = generate_unique_id(row[proc["Gender"]], existing_ids)
        new_records.at[i, proc["Profile ID"]] = new_id
        existing_ids.append(new_id)

        new_profile_key = generate_profile_key(existing_profile_key)
        new_records.at[i, proc["Profile Key"]] = new_profile_key
        existing_profile_key.append(new_profile_key)
        print(f'{row["Profile ID"]}')



    # Write new records to processed sheet
    if not new_records.empty:
        if proc_records.empty:
            # Sheet is empty → add headers + data
            proc_profile_generator.update(
                [new_records.columns.values.tolist()] + new_records.values.tolist()
            )
        else:
            # Sheet has data → append only values
            proc_profile_generator.append_rows(new_records.values.tolist())

    # Handle new profiles - create PDFs and send emails
    for i, row in new_records.iterrows():
        data = row.to_dict()
        profile_id = row[proc["Profile ID"]]
        name = row[raw['Full Name']]
        email = row[raw['Email']]
        pdf_file = create_pdf(data, profile_id)

        if row.get(proc["Profile ID"]):
            try:
                intiation_email(email, name, profile_id, pdf_file)
                print(f"📩 Profile {profile_id}: Sent NEW profile email to {email}")
            except Exception as e:
                print(f"Profile {profile_id}: Failed to send email to {email}: {e}")


    # Process amendments
    if not amm_records.empty:
        process_amendments(amm_records, proc_profile_generator, proc, amm)

    # Handle ammended profiles - create PDFs and send emails
    for i, row in amm_records.iterrows():
        data = row.to_dict()
        profile_id = row[amm["Profile ID"]]
        name = row[amm['Full Name']]
        email = row[amm['Email']]
        pdf_file = create_pdf(data, profile_id)

        if (
            row[amm['Profile ID']] in existing_ids
        ):  # if update_ref exists and the number is part of the existing_ids
            try:
                ammendment_email(email, name, profile_id, pdf_file)
                print(
                    f"📩 Profile {profile_id}: Sent AMENDMENT email to {email}"
                )
            except Exception as e:
                print(
                    f"Profile {profile_id}: Failed to send email to {email}: {e}"
                )
                
        elif row[amm['Profile ID']] not in existing_ids:
            try:
                error_email(email, name, profile_id)
                print(f"📩 Profile {user_id}: Sent ERROR email to {row['Email']}")
            except Exception as e:
                print(f"Profile {user_id}: Failed to send email to {row['Email']}: {e}")

