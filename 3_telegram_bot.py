import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from dotenv import load_dotenv
import os
from pdf2image import convert_from_path
from telegram import Bot
import asyncio
from pdf_formation import create_pdf

load_dotenv()

# -----------------------------
# CONFIGURATION
# -----------------------------
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")
POST_F_PROF = os.getenv("POST_F_PROF")
POST_M_PROF = os.getenv("POST_M_PROF")
PROC_PROFILE_GENERATOR = os.getenv("PROC_PROFILE_GENERATOR")

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# -----------------------------
# AUTHENTICATE WITH GOOGLE SHEETS
# -----------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_JSON, scope)
client = gspread.authorize(creds)

print(f"Attempting to open POST_F_PROF: '{POST_F_PROF}'")
post_f_sheet = client.open(POST_F_PROF).sheet1
print(f"✅ Successfully opened: {POST_F_PROF}")

print(f"Attempting to open POST_M_PROF: '{POST_M_PROF}'")
post_m_sheet = client.open(POST_M_PROF).sheet1
print(f"✅ Successfully opened: {POST_M_PROF}")

print(f"Attempting to open PROC_PROFILE_GENERATOR: '{PROC_PROFILE_GENERATOR}'")
proc_sheet = client.open(PROC_PROFILE_GENERATOR).sheet1
print(f"✅ Successfully opened: {PROC_PROFILE_GENERATOR}")

# -----------------------------
# GET ALL RECORDS
# -----------------------------
post_f_records = pd.DataFrame(post_f_sheet.get_all_records())
post_m_records = pd.DataFrame(post_m_sheet.get_all_records())
proc_full_records = pd.DataFrame(proc_sheet.get_all_records())

print(f"📊 Loaded {len(proc_full_records)} profiles from processed sheet")

# Combine both POST sheets
all_records = []
sheet_mapping = []  # Track which sheet each record belongs to

if not post_f_records.empty:
    for idx, row in post_f_records.iterrows():
        all_records.append(row)
        sheet_mapping.append(('female', post_f_sheet, idx))

if not post_m_records.empty:
    for idx, row in post_m_records.iterrows():
        all_records.append(row)
        sheet_mapping.append(('male', post_m_sheet, idx))

if not all_records:
    print("⚠️ No records found in POST_F_PROF or POST_M_PROF sheets")
    exit(0)

proc_records = pd.DataFrame(all_records)

# Check if sheets have the required columns
if "Posted?" not in proc_records.columns:
    print("⚠️ 'Posted?' column not found in sheets")
    exit(1)

if "Confirm?" not in proc_records.columns:
    print("⚠️ 'Confirm?' column not found in sheets. Please add a 'Confirm?' column.")
    exit(1)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

async def send_pdf_as_image(bot, chat_id, pdf_path, profile_id, representative_number, gender):
    """
    Convert PDF to image and send as photo to Telegram channel

    Args:
        bot: Telegram Bot instance
        chat_id: Telegram channel/chat ID
        pdf_path: Path to PDF file
        profile_id: Profile ID for caption
        representative_number: Representative contact number
        gender: Gender of the profile (Male/Female)

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Convert PDF to image (first page only since PDFs are single page)
        images = convert_from_path(pdf_path, dpi=300)

        if not images:
            return False, "Failed to convert PDF to image"

        # Get the first (and only) page
        image = images[0]

        # Save temporarily
        temp_image_path = pdf_path.replace('.pdf', '_temp.jpg')
        image.save(temp_image_path, 'JPEG', quality=95)

        # Create gender-specific caption
        if str(gender).lower() == 'female':
            gender_text = "this sister"
            pronoun = "her"
        else:
            gender_text = "this brother"
            pronoun = "his"

        caption = f"""
<b>Al Rawdha Matrimonial Profile</b>
<b>Profile ID:</b> {profile_id}
<b>If interested in {gender_text} contact {pronoun} representative:</b> {representative_number}
<i>May Allah guide you to the right match 💚</i>
        """.strip()

        # Send as photo
        with open(temp_image_path, 'rb') as photo:
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode='HTML'
            )
        

        # Clean up temp file
        os.remove(temp_image_path)
        return True, "Success"

    except Exception as e:
        return False, f"Error: {str(e)}"


def mark_as_posted(sheet, row_number, posted_column_index):
    """Mark a profile as posted in Google Sheets"""
    try:
        sheet.update_cell(row_number, posted_column_index, "Yes")
        return True
    except Exception as e:
        print(f"❌ Failed to mark row {row_number} as posted: {e}")
        return False


# -----------------------------
# MAIN WORKFLOW
# -----------------------------

async def main():
    """Main async function to post profiles to Telegram"""

    # Filter profiles that need to be posted
    # Condition: Posted? = "No" AND Confirm? = "Yes" (case insensitive)
    profiles_to_post_mask = (
        (proc_records["Posted?"].str.strip().str.lower() == "no") &
        (proc_records["Confirm?"].str.strip().str.lower() == "yes")
    )

    if not profiles_to_post_mask.any():
        print("✅ No profiles ready to post (all posted or not confirmed)")
        return

    profiles_to_post_indices = [i for i, mask in enumerate(profiles_to_post_mask) if mask]

    print(f"\n📋 Found {len(profiles_to_post_indices)} profile(s) ready to post to Telegram\n")

    posted_count = 0
    failed_count = 0

    # Initialize Telegram bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    for record_idx in profiles_to_post_indices:
        profile = proc_records.iloc[record_idx]
        gender, sheet, sheet_idx = sheet_mapping[record_idx]

        profile_id = profile.get("Profile ID", "Unknown")
        representative_number = profile.get("Representative's Number", "Unknown")

        print(f"📤 Posting Profile ID: {profile_id} ({gender})")

        # Get full profile data from processed sheet
        full_profile = proc_full_records[proc_full_records["Profile ID"] == profile_id]

        if full_profile.empty:
            print(f"   ⚠️ Profile ID {profile_id} not found in processed sheet, skipping...")
            failed_count += 1
            continue

        # Create PDF from full profile data
        try:
            data = full_profile.iloc[0].to_dict()
            pdf_path = create_pdf(data, profile_id)
            print(f"   ✅ Created PDF: {pdf_path}")
        except Exception as e:
            print(f"   ❌ Failed to create PDF: {e}")
            failed_count += 1
            continue

        # Send to Telegram as image
        gender = data.get('Gender', '')
        success, message = await send_pdf_as_image(bot, TELEGRAM_CHANNEL_ID, pdf_path, profile_id, representative_number, gender)

        if success:
            print(f"   ✅ Successfully posted to Telegram as image")

            # Mark as posted in Google Sheets
            # Get column index for "Posted?" from the correct sheet
            headers = sheet.row_values(1)
            posted_column_index = headers.index("Posted?") + 1

            # Calculate sheet row number (DataFrame index + 2: +1 for 0-index, +1 for header)
            sheet_row = sheet_idx + 2

            if mark_as_posted(sheet, sheet_row, posted_column_index):
                print(f"   ✅ Marked as posted in Google Sheets")
                posted_count += 1
            else:
                print(f"   ⚠️ Posted to Telegram but failed to mark in sheet")
                failed_count += 1
        else:
            print(f"   ❌ Failed to post: {message}")
            failed_count += 1

    print(f"\n{'='*50}")
    print(f"📊 SUMMARY:")
    print(f"   ✅ Successfully posted: {posted_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📝 Total processed: {len(profiles_to_post_indices)}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(main())
