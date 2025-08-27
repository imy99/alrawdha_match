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
    # raw_records["Timestamp"] = pd.to_datetime(raw_records["Timestamp"])
    new_records = raw_records
    
else:
    raw_records["Timestamp"] = pd.to_datetime(raw_records["Timestamp"]).dt.strftime("%Y/%m/%d %H:%M:%S")
    proc_records["Timestamp"] = pd.to_datetime(proc_records["Timestamp"]).dt.strftime("%Y/%m/%d %H:%M:%S")

    latest_proc_time = proc_records["Timestamp"].max()
    new_records = raw_records[raw_records["Timestamp"] > latest_proc_time]
    new_records["Timestamp"] = new_records["Timestamp"].astype(str)

new_records.insert(0, "Profile ID","")


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------


def process_amendments(df):
    """
    Update existing profiles with amendment rows and safely remove amendment rows
    after merging their data into the matching Profile ID row.
    """
    import pandas as pd

    # Load sheet into DataFrame
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
            print(profile_id)
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
   
    # Generating Profile ID's
    if proc_records.empty:
        existing_ids = []
    else:
        existing_ids = proc_records['Profile ID'].to_list()

    for i, row in new_records.iterrows():
        if not row["Profile ID"] and not row["If updating, add Profile ID (from email)"]:
            gender = row["Gender"]
            new_id = generate_unique_id(gender, existing_ids)
            new_records.at[i, "Profile ID"] = new_id
            existing_ids.append(new_id)
            print(row["Profile ID"])
    

    for index, row in new_records.iterrows():
        new_records = process_amendments(new_records)

    

    # Handle new profiles
    for _, row in new_records.iterrows():
        data = row.to_dict()
        user_id = row["Profile ID"]
        pdf_file = create_pdf(data, user_id)
        try:
            send_email(data["Email"], user_id, pdf_file)
            print(f"📩 Sent NEW profile email to {data['Email']}")
        except Exception as e:
            print(f"Failed to send email to {data['Email']}: {e}")

    # Handle amended profiles
    for _, row in new_records.iterrows():
        data = row.to_dict()
        user_id = row["Profile ID"]
        pdf_file = create_pdf(data, user_id)
        try:
            send_email(data["Email"], user_id, pdf_file)  # you can customize subject
            print(f"📩 Sent AMENDMENT email to {data['Email']}")
        except Exception as e:
            print(f"Failed to send email to {data['Email']}: {e}")

    if proc_records.empty:
        # Sheet is empty → add headers + data
        proc_sheet.update([new_records.columns.values.tolist()] + new_records.values.tolist())
    else:
        # Sheet has data → append only values
        proc_sheet.append_rows(new_records.values.tolist())


    # print(f"Profile created and emailed to {new_records['Email']} with ID {row["Profile ID"]}")
