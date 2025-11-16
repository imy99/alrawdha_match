import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from dotenv import load_dotenv
import os
import yaml

load_dotenv()

# Load config.yaml
with open("category_names.yaml", "r") as file:
    config = yaml.safe_load(file)

# PROC_PROFILE_GENERATOR (variables)
proc = config['3ab']

# -----------------------------
# CONFIGURATION
# -----------------------------
# Path to your service account JSON key
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

# Google Sheet names
PROC_PROFILE_GENERATOR = os.getenv("PROC_PROFILE_GENERATOR")
POST_F_PROF = os.getenv("POST_F_PROF")
POST_M_PROF = os.getenv("POST_M_PROF")

# -----------------------------
# AUTHENTICATE WITH GOOGLE SHEETS
# -----------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_JSON, scope)
client = gspread.authorize(creds)

proc_profile_generator = client.open(PROC_PROFILE_GENERATOR).sheet1
post_f_prof = client.open(POST_F_PROF).sheet1
post_m_prof = client.open(POST_M_PROF).sheet1

print(
    "Authenticated! Read from:",
    PROC_PROFILE_GENERATOR.title(),
    "| Write to:",
    POST_F_PROF.title(),
    "and",
    POST_M_PROF.title(),
)

# -----------------------------
# LOAD PROCESSED PROFILES
# -----------------------------

def load_sheets(sheet):
    df = pd.DataFrame(sheet.get_all_records())
    if df.empty:
        headers = sheet.row_values(1)
        df = pd.DataFrame(columns=headers)
    return df

proc_records = load_sheets(proc_profile_generator)
post_f_records = load_sheets(post_f_prof)
post_m_records = load_sheets(post_m_prof)

print(f"📊 Loaded {len(proc_records)} processed profiles")

# -----------------------------
# MAIN WORKFLOW
# -----------------------------
if __name__ == "__main__":

    # Select specific columns from processed profiles
    columns_to_keep = [
        proc["Timestamp"],
        proc["Ammended Timestamp"],
        proc["Profile ID"],
        proc["Profile Key"],
        proc["Full Name"],
        proc["Gender"],
        proc["Email"],
        proc["Phone Number"]
    ]

    # Filter only the columns we need
    selected_records = proc_records[columns_to_keep].copy()

    # Insert new columns at the beginning
    selected_records.insert(0, "Confirm?", "No")
    selected_records.insert(1, "Posted?", "No")

    print(f"📋 Selected columns: {selected_records.columns.tolist()}")

    # Separate by gender
    female_records = selected_records[selected_records[proc["Gender"]] == "Female"].copy()
    male_records = selected_records[selected_records[proc["Gender"]] == "Male"].copy()

    print(f"👩 Female profiles: {len(female_records)}")
    print(f"👨 Male profiles: {len(male_records)}")

    # Process existing profiles - update if processed sheet is newer
    profiles_to_update_f = []
    profiles_to_update_m = []

    if not post_f_records.empty:
        # Convert timestamps to datetime for comparison
        post_f_records[proc["Timestamp"]] = pd.to_datetime(post_f_records[proc["Timestamp"]], format='mixed', dayfirst=True, errors='coerce')
        post_f_records[proc["Ammended Timestamp"]] = pd.to_datetime(post_f_records[proc["Ammended Timestamp"]], format='mixed', dayfirst=True, errors='coerce')

        for idx, f_row in female_records.iterrows():
            profile_id = f_row[proc["Profile ID"]]
            existing = post_f_records[post_f_records[proc["Profile ID"]] == profile_id]

            if not existing.empty:
                # Get most recent timestamp from both sheets
                proc_timestamps = [f_row[proc["Timestamp"]], f_row[proc["Ammended Timestamp"]]]
                proc_timestamps = [pd.to_datetime(t, format='mixed', dayfirst=True, errors='coerce') for t in proc_timestamps if pd.notna(t) and str(t).strip()]
                proc_max_time = max([t for t in proc_timestamps if pd.notna(t)]) if proc_timestamps else None

                post_timestamps = [existing.iloc[0][proc["Timestamp"]], existing.iloc[0][proc["Ammended Timestamp"]]]
                post_timestamps = [t for t in post_timestamps if pd.notna(t) and str(t).strip()]
                post_max_time = max([t for t in post_timestamps if pd.notna(t)]) if post_timestamps else None

                # If processed sheet is newer, mark for update
                if proc_max_time and post_max_time and proc_max_time > post_max_time:
                    sheet_row = existing.index[0] + 2  # +2 for header and 0-index
                    profiles_to_update_f.append((sheet_row, f_row))
                    # Remove from new records since we're updating existing
                    female_records = female_records.drop(idx)
                else:
                    # Remove from new records since it already exists and is up to date
                    female_records = female_records.drop(idx)

        print(f"   Female profiles to update: {len(profiles_to_update_f)}")
        print(f"   New female profiles to add: {len(female_records)}")
    else:
        print(f"   New female profiles to add: {len(female_records)}")

    if not post_m_records.empty:
        # Convert timestamps to datetime for comparison
        post_m_records[proc["Timestamp"]] = pd.to_datetime(post_m_records[proc["Timestamp"]], format='mixed', dayfirst=True, errors='coerce')
        post_m_records[proc["Ammended Timestamp"]] = pd.to_datetime(post_m_records[proc["Ammended Timestamp"]], format='mixed', dayfirst=True, errors='coerce')

        for idx, m_row in male_records.iterrows():
            profile_id = m_row[proc["Profile ID"]]
            existing = post_m_records[post_m_records[proc["Profile ID"]] == profile_id]

            if not existing.empty:
                # Get most recent timestamp from both sheets
                proc_timestamps = [m_row[proc["Timestamp"]], m_row[proc["Ammended Timestamp"]]]
                proc_timestamps = [pd.to_datetime(t, format='mixed', dayfirst=True, errors='coerce') for t in proc_timestamps if pd.notna(t) and str(t).strip()]
                proc_max_time = max([t for t in proc_timestamps if pd.notna(t)]) if proc_timestamps else None

                post_timestamps = [existing.iloc[0][proc["Timestamp"]], existing.iloc[0][proc["Ammended Timestamp"]]]
                post_timestamps = [t for t in post_timestamps if pd.notna(t) and str(t).strip()]
                post_max_time = max([t for t in post_timestamps if pd.notna(t)]) if post_timestamps else None

                # If processed sheet is newer, mark for update
                if proc_max_time and post_max_time and proc_max_time > post_max_time:
                    sheet_row = existing.index[0] + 2  # +2 for header and 0-index
                    profiles_to_update_m.append((sheet_row, m_row))
                    # Remove from new records since we're updating existing
                    male_records = male_records.drop(idx)
                else:
                    # Remove from new records since it already exists and is up to date
                    male_records = male_records.drop(idx)

        print(f"   Male profiles to update: {len(profiles_to_update_m)}")
        print(f"   New male profiles to add: {len(male_records)}")
    else:
        print(f"   New male profiles to add: {len(male_records)}")

    # Update existing female profiles
    if profiles_to_update_f:
        headers = post_f_prof.row_values(1)
        for sheet_row, row_data in profiles_to_update_f:
            # Reset Posted? and Confirm? to "No"
            row_data["Posted?"] = "No"
            row_data["Confirm?"] = "No"

            # Update entire row
            row_values = [row_data.get(col, "") for col in headers]
            for col_idx, value in enumerate(row_values, start=1):
                post_f_prof.update_cell(sheet_row, col_idx, str(value) if pd.notna(value) else "")

            print(f"✅ Updated female profile {row_data[proc['Profile ID']]} (Posted? and Confirm? reset to No)")

    # Write female profiles to POST_F_PROF
    if not female_records.empty:
        if post_f_records.empty:
            # Sheet is empty → add headers + data
            post_f_prof.update(
                [female_records.columns.values.tolist()] + female_records.values.tolist()
            )
            print(f"✅ Wrote {len(female_records)} female profiles (with headers)")
        else:
            # Sheet has data → append only values
            post_f_prof.append_rows(female_records.values.tolist())
            print(f"✅ Appended {len(female_records)} female profiles")
    else:
        print("ℹ️  No new female profiles to add")

    # Update existing male profiles
    if profiles_to_update_m:
        headers = post_m_prof.row_values(1)
        for sheet_row, row_data in profiles_to_update_m:
            # Reset Posted? and Confirm? to "No"
            row_data["Posted?"] = "No"
            row_data["Confirm?"] = "No"

            # Update entire row
            row_values = [row_data.get(col, "") for col in headers]
            for col_idx, value in enumerate(row_values, start=1):
                post_m_prof.update_cell(sheet_row, col_idx, str(value) if pd.notna(value) else "")

            print(f"✅ Updated male profile {row_data[proc['Profile ID']]} (Posted? and Confirm? reset to No)")

    # Write male profiles to POST_M_PROF
    if not male_records.empty:
        if post_m_records.empty:
            # Sheet is empty → add headers + data
            post_m_prof.update(
                [male_records.columns.values.tolist()] + male_records.values.tolist()
            )
            print(f"✅ Wrote {len(male_records)} male profiles (with headers)")
        else:
            # Sheet has data → append only values
            post_m_prof.append_rows(male_records.values.tolist())
            print(f"✅ Appended {len(male_records)} male profiles")
    else:
        print("ℹ️  No new male profiles to add")

    print("\n✅ Profile check and separation complete!")
