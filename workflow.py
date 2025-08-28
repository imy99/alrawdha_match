import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import random
from email_formation import intiation_email, error_email, ammendment_email
from pdf_formation import create_pdf
from dotenv import load_dotenv
import os

load_dotenv()

# -----------------------------
# CONFIGURATION
# -----------------------------
# Path to your service account JSON key
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

# Google Sheet name (linked to your Form responses)
RAW_SHEET_NAME = os.getenv("RAW_SHEET_NAME")
PROC_SHEET_NAME = os.getenv("PROC_SHEET_NAME")

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
raw_sheet = client.open(RAW_SHEET_NAME).sheet1
proc_sheet = client.open(PROC_SHEET_NAME).sheet1
print(
    "Authenticated! Read from:",
    RAW_SHEET_NAME.title(),
    "| Write to:",
    PROC_SHEET_NAME.title(),
)

# -----------------------------
# GET ALL RECORDS
# -----------------------------
raw_records = pd.DataFrame(raw_sheet.get_all_records())  # returns a list of dicts
proc_records = pd.DataFrame(proc_sheet.get_all_records())

# Filter newer records
if proc_records.empty:
    new_records = raw_records

else:
    raw_records["Timestamp"] = pd.to_datetime(
        raw_records["Timestamp"], dayfirst=True
    ).dt.strftime("%d/%m/%Y %H:%M:%S")
    proc_records["Timestamp"] = pd.to_datetime(
        proc_records["Timestamp"], dayfirst=True
    ).dt.strftime("%d/%m/%Y %H:%M:%S")

    latest_proc_time = proc_records["Timestamp"].max()
    new_records = raw_records[raw_records["Timestamp"] > latest_proc_time].copy()
    new_records["Timestamp"] = new_records["Timestamp"].astype(str)

new_records.insert(1, "Profile ID", "")
new_records.columns = [col.strip() for col in new_records.columns]


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------


def process_amendments(proc_sheet):
    """
    Update existing profiles with amendment rows directly on the Google Sheet.
    Any row with a value in "If updating, add Profile ID (from email)" will update
    the matching Profile ID row, then the amendment row is deleted.
    """
    # Load all sheet values
    rows = proc_sheet.get_all_values()
    headers = rows[0]

    # Column indices
    profile_id_col = headers.index("Profile ID")
    update_ref_col = headers.index("If updating, add Profile ID (from email)")

    rows_to_delete = []

    # Iterate over rows (skip header)
    for i, row in enumerate(rows[1:], start=2):  # gspread is 1-indexed
        amendment_ref = row[update_ref_col].strip()

        if amendment_ref:
            # Find matching Profile ID row
            match_row_index = None
            for j, r in enumerate(rows[1:], start=2):
                if r[profile_id_col].strip() == amendment_ref:
                    match_row_index = j
                    break

            if match_row_index:
                # Update matching row with non-empty values from amendment
                for col_idx, value in enumerate(row):
                    if col_idx != profile_id_col and col_idx != update_ref_col:
                        if value.strip():
                            proc_sheet.update_cell(match_row_index, col_idx + 1, value)
                print(f"✅ Updated Profile ID {amendment_ref} from row {i}")

                # Mark amendment row for deletion
                rows_to_delete.append(i)
            else:
                print(
                    f"⚠️ No matching Profile ID found for amendment row {i}, skipping..."
                )

    # Delete amendment rows from bottom to top
    for r in sorted(rows_to_delete, reverse=True):
        proc_sheet.delete_rows(r)
        print(f"🗑️ Deleted amendment row {r}")


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
    else:
        existing_ids = proc_records["Profile ID"].to_list()

    for i, row in new_records.iterrows():
        if (
            not row["Profile ID"]
            and not row["If updating, add Profile ID (from email)"]
        ):
            gender = row["Gender"]
            new_id = generate_unique_id(gender, existing_ids)
            new_records.at[i, "Profile ID"] = new_id
            existing_ids.append(new_id)
            print(row["Profile ID"])

    # Handle new profiles
    existing_ids = set()

    if not proc_records.empty:
        existing_ids.update(proc_records["Profile ID"].dropna().tolist())

    # Add IDs from new_records that might already exist
    existing_ids.update(new_records["Profile ID"].dropna().tolist())

    for _, row in new_records.iterrows():
        data = row.to_dict()
        user_id = row["Profile ID"]
        ammended_id = row["If updating, add Profile ID (from email)"]
        name = row["Full Name (will be kept anonymous)"]
        pdf_file = create_pdf(data, user_id)

        update_ref = row.get("If updating, add Profile ID (from email)")

        if (
            update_ref and update_ref in existing_ids
        ):  # if update_ref exists and the number is part of the existing_ids
            try:
                ammendment_email(row["Email"], name, ammended_id, pdf_file)
                print(
                    f"📩 Profile {ammended_id}: Sent AMENDMENT email to {data['Email']}"
                )
            except Exception as e:
                print(
                    f"Profile {ammended_id}: Failed to send email to {row['Email']}: {e}"
                )
        elif row.get("Profile ID"):
            try:
                intiation_email(row["Email"], name, user_id, pdf_file)
                print(f"📩 Profile {user_id}: Sent NEW profile email to {row['Email']}")
            except Exception as e:
                print(f"Profile {user_id}: Failed to send email to {row['Email']}: {e}")
        elif update_ref not in existing_ids:
            try:
                error_email(row["Email"], name, user_id, pdf_file)
                print(f"📩 Profile {user_id}: Sent ERROR email to {row['Email']}")
            except Exception as e:
                print(f"Profile {user_id}: Failed to send email to {row['Email']}: {e}")

    if proc_records.empty:
        # Sheet is empty → add headers + data
        proc_sheet.update(
            [new_records.columns.values.tolist()] + new_records.values.tolist()
        )
    else:
        # Sheet has data → append only values
        proc_sheet.append_rows(new_records.values.tolist())

    process_amendments(proc_sheet)
