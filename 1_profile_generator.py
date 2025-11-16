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
import warnings

# Ignore FutureWarning about dtype incompatibility
warnings.filterwarnings('ignore', category=FutureWarning)

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
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

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
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_JSON, scope)
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

# Rename columns from raw (2a) to proc (3ab) using shared keys
column_rename_map = {}
for key in raw.keys():
    if key in proc:  # If the key exists in both raw and proc configs
        column_rename_map[raw[key]] = proc[key]

new_records.rename(columns=column_rename_map, inplace=True)


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
    Uses proc and amm config dicts to map between sheet column names.
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

    # Get amendment sheet headers and ensure "Amendment Status" column exists
    amm_headers = amm_profile_generator.row_values(1)
    if "Amendment Status" not in amm_headers:
        # Add new column header
        amm_headers.append("Amendment Status")
        amm_profile_generator.update([amm_headers], range_name='1:1')
    amm_status_col = amm_headers.index("Amendment Status") + 1  # 1-indexed for gspread

    for idx, amm_row in amm_records.iterrows():
        # Calculate amendment sheet row number (idx + 2 because: +1 for header, +1 for 0-based to 1-based)
        amm_sheet_row = idx + 2

        # Normalize Profile ID and Key: strip whitespace and uppercase
        profile_id = str(amm_row.get(amm["Profile ID"], "")).strip().upper()
        profile_key = str(amm_row.get(amm["Profile Key"], "")).lstrip("'").lstrip().strip()

        data = amm_row.to_dict()
        name = amm_row[amm['Full Name']]
        email = amm_row[amm['Email']]
        pdf_file = create_pdf(data, profile_id)
        if not profile_id:
            continue

        # Update the normalized Profile ID and Key back to the dataframe
        amm_records.at[idx, amm["Profile ID"]] = profile_id
        amm_records.at[idx, amm["Profile Key"]] = profile_key

        # Find row number in sheet (skip header → start at row 1)
        row_num = None
        for i in range(1, len(rows)):
            if rows[i][col_index[proc["Profile ID"]]] == profile_id and rows[i][col_index[proc["Profile Key"]]] == profile_key:
                row_num = i + 1   # convert to 1-indexed for gspread
                row_data = rows[i]
                break

        # If profile not found or key mismatch, send error email
        if row_num is None:
            # Mark as Failed in amendment sheet
            amm_profile_generator.update_cell(amm_sheet_row, amm_status_col, "Failed")

            try:
                print(f"⚠️ Profile ID {profile_id} not found or key mismatch in processed sheet.")
                error_email(email, name, profile_id, profile_key)
                print(f"📩 Profile {profile_id}: Sent ERROR email")
            except Exception as e:
                print(f"Profile {profile_id}: Failed to send error email: {e}")
            continue

        style = str(amm_row.get(amm["Amendment Style"], "")).strip()
        print(f"🔍 Processing Profile ID {profile_id} with style: '{style}'")

        updates_made = 0
        column_name_list = []
        for col_name in headers:
            if col_name in protected:
                continue

            # Find the key in proc config that matches this column name
            proc_key = None
            for key, value in proc.items():
                if value == col_name:
                    proc_key = key
                    break

            # Skip if no key found (column not in config)
            if proc_key is None:
                print(f"  ⚠️  WARNING: Column '{col_name}' not found in proc config - skipping")
                continue

            # Get the corresponding amendment sheet column name using the same key
            amm_col_name = amm.get(proc_key)

            # Replace completely → always update ALL fields (even if empty or not in amm)
            if "Replace PDF completely" in style:
                # Get value from amendment sheet, or empty string if no mapping
                new_value = amm_row.get(amm_col_name, "") if amm_col_name else ""

                column_name_list.append(col_name)
                proc_profile_generator.update_cell(
                    row_num,
                    col_index[col_name] + 1,
                    str(new_value) if new_value else ""
                )
                updates_made += 1

            # Keep existing → only update if new data is non-empty
            elif "Keep existing" in style:
                # Skip if no mapping exists for this key in amm
                if amm_col_name is None:
                    continue

                # Get the value from amendment sheet using the mapped column name
                new_value = amm_row.get(amm_col_name, "")

                if new_value and str(new_value).strip():
                    column_name_list.append(col_name)
                    proc_profile_generator.update_cell(
                        row_num,
                        col_index[col_name] + 1,
                        str(new_value)
                    )
                    updates_made += 1

        # Amendment timestamp update
        ammend_time_val = amm_row.get(amm["Ammended Timestamp"], "")
        if ammend_time_val and str(ammend_time_val).strip():
            proc_profile_generator.update_cell(
                row_num,
                col_index[proc["Ammended Timestamp"]] + 1,
                str(ammend_time_val)
            )

        print(f"📊 Updated Profile ID {profile_id} with {updates_made} fields: ({column_name_list})")

        # Mark as Complete in amendment sheet and send email
        amm_profile_generator.update_cell(amm_sheet_row, amm_status_col, "Complete")

        try:
            ammendment_email(email, name, profile_id, profile_key, pdf_file)
            print(f"📩 Profile {profile_id}: Sent AMENDMENT email to {email}")
        except Exception as e:
            print(f"Profile {profile_id}: Failed to send amendment email: {e}")



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
        name = row[proc['Full Name']]
        email = row[proc['Email']]
        pdf_file = create_pdf(data, profile_id)

        if row.get(proc["Profile ID"]):
            try:
                intiation_email(email, name, profile_id, pdf_file)
                print(f"📩 Profile {profile_id}: Sent NEW profile email")
            except Exception as e:
                print(f"Profile {profile_id}: Failed to send email")


    # Process amendments
    amm_records = amm_records[amm_records[amm['Amendment Status']].isnull()]
    print(f"\n📋 Amendment records found: {len(amm_records)}")
    if not amm_records.empty:
        print("Starting amendment processing...")
        process_amendments(amm_records, proc_profile_generator, proc, amm)
    else:
        print("No amendments to process.")


                

