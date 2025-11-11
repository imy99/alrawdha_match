import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from dotenv import load_dotenv
import os
from pdf2image import convert_from_path
from telegram import Bot
import asyncio

load_dotenv()

# -----------------------------
# CONFIGURATION
# -----------------------------
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
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
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(creds)

print(f"Attempting to open PROC_PROFILE_GENERATOR: '{PROC_PROFILE_GENERATOR}'")
proc_profile_generator_sheet = client.open(PROC_PROFILE_GENERATOR).sheet1
print(f"✅ Successfully opened: {PROC_PROFILE_GENERATOR}")

# -----------------------------
# GET ALL RECORDS
# -----------------------------
proc_records = pd.DataFrame(proc_profile_generator_sheet.get_all_records())

# Check if sheet has the required columns
if proc_records.empty:
    print("⚠️ No records found in processed profile generator sheet")
    exit(0)

if "Posted?" not in proc_records.columns:
    print("⚠️ 'Posted?' column not found in sheet")
    exit(1)

if "Confirm?" not in proc_records.columns:
    print("⚠️ 'Confirm?' column not found in sheet. Please add a 'Confirm?' column to your sheet.")
    exit(1)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

async def send_pdf_as_image(bot, chat_id, pdf_path, profile_id):
    """
    Convert PDF to image and send as photo to Telegram channel

    Args:
        bot: Telegram Bot instance
        chat_id: Telegram channel/chat ID
        pdf_path: Path to PDF file
        profile_id: Profile ID for caption

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

        # Create caption
        caption = f"""
🌙 <b>Al Rawdha Matrimonial Profile</b>
<b>Profile ID:</b> {profile_id}
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
        sheet.update_cell(row_number, posted_column_index, "yes")
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
    profiles_to_post = proc_records[
        (proc_records["Posted?"].str.strip().str.lower() == "no") &
        (proc_records["Confirm?"].str.strip().str.lower() == "yes")
    ]

    if profiles_to_post.empty:
        print("✅ No profiles ready to post (all posted or not confirmed)")
        return

    print(f"\n📋 Found {len(profiles_to_post)} profile(s) ready to post to Telegram\n")

    # Get column index for "Posted?" (1-indexed for gspread)
    headers = proc_profile_generator_sheet.row_values(1)
    posted_column_index = headers.index("Posted?") + 1

    posted_count = 0
    failed_count = 0

    # Initialize Telegram bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    for idx, profile in profiles_to_post.iterrows():
        profile_id = profile.get("Profile ID", "Unknown")
        pdf_path = profile.get("PDF Path", "")

        print(f"📤 Posting Profile ID: {profile_id}")

        # Check if PDF path exists
        if not pdf_path or pd.isna(pdf_path):
            print(f"   ⚠️ No PDF path found for {profile_id}, skipping...")
            failed_count += 1
            continue

        # Check if file exists
        if not os.path.exists(pdf_path):
            print(f"   ⚠️ PDF file not found: {pdf_path}, skipping...")
            failed_count += 1
            continue

        # Send to Telegram as image
        success, message = await send_pdf_as_image(bot, TELEGRAM_CHANNEL_ID, pdf_path, profile_id)

        if success:
            print(f"   ✅ Successfully posted to Telegram as image")

            # Mark as posted in Google Sheets
            # Calculate sheet row number (DataFrame index + 2: +1 for 0-index, +1 for header)
            sheet_row = idx + 2

            if mark_as_posted(proc_profile_generator_sheet, sheet_row, posted_column_index):
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
    print(f"   📝 Total processed: {len(profiles_to_post)}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(main())
