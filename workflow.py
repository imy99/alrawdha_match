import gspread
from oauth2client.service_account import ServiceAccountCredentials
import uuid
from fpdf import FPDF
import yagmail
import pandas as pd
import random

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
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(creds)
raw_sheet = client.open(RAW_SHEET_NAME).sheet1
proc_sheet = client.open(PROC_SHEET_NAME).sheet1
print("Authenticated! Read from:", raw_sheet.title, "| Write to:", proc_sheet.title)

# -----------------------------
# GET ALL RECORDS
# -----------------------------
raw_records = pd.DataFrame(raw_sheet.get_all_records())  # returns a list of dicts
proc_records = pd.DataFrame(proc_sheet.get_all_records())

# Filter newer records
if proc_records.empty:
    raw_records["Timestamp"] = pd.to_datetime(raw_records["Timestamp"])
    new_records = raw_records
else:
    raw_records["Timestamp"] = pd.to_datetime(raw_records["Timestamp"])
    proc_records["Timestamp"] = pd.to_datetime(proc_records["Timestamp"])

    latest_proc_time = proc_records["Timestamp"].max()
    new_records = raw_records[raw_records["Timestamp"] > latest_proc_time]
    new_records.insert(0, "Profile ID","")


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def save_submission(data):
    """Save submission to Google Sheet and return unique ID"""
    # Check if updating existing profile
    
    for i, row in enumerate(data):
        ref_code = row['If updating, add Profile ID (from email)'].astype(int)
        
        if ref_code:
            if row['Profile ID'].astype(int) == ref_code:
                # Update existing row
                row_number = i + 2  # +2 because gspread counts header row
                for j, key in enumerate(data.keys(), start=3):  # Assuming ID is column 1
                    sheet.update_cell(row_number, j, data[key])
                return data['Profile ID']
            
SNAPSHOT_FILE = "profiles_snapshot.csv"

def load_snapshot():
    """Load previous snapshot if it exists, else empty DataFrame"""
    if os.path.exists(SNAPSHOT_FILE):
        return pd.read_csv(SNAPSHOT_FILE)
    return pd.DataFrame()

df_old = load_snapshot()

def detect_changes(df_current, df_old):
    """Return two DataFrames: new_rows, amended_rows"""
    if df_old.empty:
        return df_current, pd.DataFrame()  # everything is new

    # Ensure Profile ID column exists
    if "Profile ID" not in df_current.columns:
        return pd.DataFrame(), pd.DataFrame()

    # New rows = those with Profile ID not in old snapshot
    new_rows = df_current[~df_current["Profile ID"].isin(df_old["Profile ID"])]

    # Amended rows = those with matching ID but changed fields
    amended_rows = pd.DataFrame()
    for _, row in df_current.iterrows():
        pid = row["Profile ID"]
        if pid in df_old["Profile ID"].values:
            old_row = df_old[df_old["Profile ID"] == pid].iloc[0]
            if not row.equals(old_row):
                amended_rows = pd.concat([amended_rows, row.to_frame().T])

    return new_rows, amended_rows

def save_snapshot(df):
    """Save current DataFrame as snapshot"""
    df.to_csv(SNAPSHOT_FILE, index=False)

def process_amendments(sheet):
    """
    Update existing profiles with amendment rows and safely remove amendment rows
    after merging their data into the matching Profile ID row.
    """
    import pandas as pd

    # Load sheet into DataFrame
    rows = sheet.get_all_values()
    df = pd.DataFrame(rows[1:], columns=rows[0])

    rows_to_delete = []

    for i, row in df.iterrows():
        # Get amendment reference code
        amendment_ref = row.get("If updating, add Profile ID (from email)")
        
        if amendment_ref:  # This row is an amendment
            # Find the existing row with Profile ID matching the reference
            existing_index = df.index[df["Profile ID"] == amendment_ref].tolist()
            
            if existing_index:
                idx = existing_index[0]  # row index of the original profile

                # ✅ Update only if amendment has non-empty values
                for col in df.columns:
                    if col not in ["Profile ID", amendment_ref]:
                        if row[col]:  # only overwrite if amendment provided a value
                            df.at[idx, col] = row[col]
                            col_index = df.columns.get_loc(col) + 1
                            sheet.update_cell(idx + 2, col_index, row[col])

                print(f"✅ Updated Profile ID {amendment_ref} with amendment from row {i+2}")

                # ✅ Only mark amendment row for deletion AFTER update
                rows_to_delete.append(i + 2)

            else:
                print(f"⚠️ No matching Profile ID found for amendment row {i+2}, skipping...")

    # Delete amendment rows from bottom to top (avoid shifting issues)
    for r in sorted(rows_to_delete, reverse=True):
        sheet.delete_rows(r)
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


def create_pdf(data, user_id):
    """Create a professional PDF profile for the user"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 15, f"Dating Profile ID: {user_id}", ln=True, align='C')
    pdf.ln(10)  # space after title

    # Profile details
    pdf.set_font("Arial", '', 12)
    for key, value in data.items():
        # Key in bold
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(50, 10, f"{key}:", ln=0)
        # Value in normal font
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, f"{value}")
        pdf.ln(2)  # small space between rows

    # Optional: add a line separator at the end
    pdf.ln(5)
    pdf.set_draw_color(0, 0, 0)  # black
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    # Save PDF
    filename = f"profile_{user_id}.pdf"
    pdf.output(filename)
    return filename



    pdf.ln(5)

    # Footer
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "This profile is shared anonymously with Al Rawdha community for matchmaking.\n"
                    "If you wish to amend your profile, use your Profile ID from the email.", ln=True, align='C')

    # Save PDF
    filename = f"profile_{user_id}.pdf"
    pdf.output(filename)
    return filename



def send_email(to_email, user_id, pdf_file):
    """Send email with ID and PDF attachment"""
    yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)
    subject = "Al Rawdha Matrimonial Profile"
    body = f"""Hello,

Your unique profile ID is: {user_id}
You can use this ID to update your profile in the future.

Attached is your profile PDF.
"""
    yag.send(to=to_email, subject=subject, contents=body, attachments=pdf_file)


# -----------------------------
# MAIN WORKFLOW
# -----------------------------
if __name__ == "__main__":
    # Example submission data from Google Form
    
    for index, row in new_records.iterrows():
        data = row.to_dict()

        process_amendments(sheet)
        save_snapshot(df)

        # Save submission
        user_id = save_submission(data)

        # Detect changes
    new_rows, amended_rows = detect_changes(df, df_old)

    headers = sheet.row_values(1)
    profile_col_index = headers.index("Profile ID") + 1
    existing_ids = list(df['Profile ID'])

    for i, row in df.iterrows():
        if not row.get("Profile ID"):
            gender = row["Gender"]
            new_id = generate_unique_id(gender, existing_ids)
            df.at[i, "Profile ID"] = new_id
            sheet.update_cell(i + 2, profile_col_index, new_id)

        #     # Create PDF
        # pdf_file = create_pdf(data, user_id)

    # Handle new profiles
    for _, row in new_rows.iterrows():
        data = row.to_dict()
        user_id = row["Profile ID"]
        pdf_file = create_pdf(data, user_id)
        try:
            send_email(data["Email"], user_id, pdf_file)
            print(f"📩 Sent NEW profile email to {data['Email']}")
        except Exception as e:
            print(f"Failed to send email to {data['Email']}: {e}")

    # Handle amended profiles
    for _, row in amended_rows.iterrows():
        data = row.to_dict()
        user_id = row["Profile ID"]
        pdf_file = create_pdf(data, user_id)
        try:
            send_email(data["Email"], user_id, pdf_file)  # you can customize subject
            print(f"📩 Sent AMENDMENT email to {data['Email']}")
        except Exception as e:
            print(f"Failed to send email to {data['Email']}: {e}")

    # Save snapshot for next run
    save_snapshot(df)


    print(f"Profile created and emailed to {data['Email']} with ID {user_id}")
