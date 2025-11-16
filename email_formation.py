import os
import yagmail
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Gmail credentials for sending emails (can use App Password)
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # Replace with your app password


def intiation_email(to_email, name, profile_id, profile_key, pdf_file):
    """Send first-time profile creation email with PDF attachment"""
    yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)
    subject = f'🎉 Welcome to Al Rawdha! Your Matrimonial Profile is Ready {datetime.now().strftime("%d/%m/%y")}'

    body = f"""Assalamu Alaykum {name},

Your Al Rawdha Matrimonial Profile has been successfully created.
Attached is your professionally prepared profile PDF. Feel free to review it and ensure everything looks correct. 
This is the version that will be shared anonymously through our Al Rawdha Matrimonial WhatsApp Broadcast, insha’Allah.

✨ Your unique Profile ID: {profile_id}
🔐 Your unique Profile Key: {profile_key}

The above details give you access to update or refine your profile in the future.
Please keep your Profile Key safe and private,  it’s your personal way to securely manage your information.

Attached is your profile PDF for your reference. Please review it and this will be sent on our AlRawdha Matrimonial WhatsApp Broadcast.

May Allah bless your efforts and guide you towards the right match.

Warm regards,
Al Rawdha Community Matchmaking
"""
    yag.send(to=to_email, subject=subject, contents=body, attachments=pdf_file)


def error_email(to_email, name, profile_id, profile_key):
    """
    Send an error email if the user entered an invalid Profile ID
    in the 'If updating, add Profile ID (from email)' field.
    """
    yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)
    subject = (
        f'⚠️ Al Rawdha Matrimonial Ammendment Error {datetime.now().strftime("%d/%m/%y")}'
    )
    body = f"""Assalamu Alaykum {name},

It looks like either the Profile ID ({profile_id}), the Profile Key ({profile_key}), or both are incorrect.

If you are trying to amend an existing profile, please use the correct Profile ID and Profile Key that were emailed to you when your profile was first created.

Warm regards,
Al Rawdha Community Matrimonal Team
"""
    yag.send(to=to_email, subject=subject, contents=body)


def ammendment_email(to_email, name, profile_id, profile_key, pdf_file):
    """Send email with ID and PDF attachment"""
    yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)
    subject = f'📝 Al Rawdha Profile Updated Successfully {datetime.now().strftime("%d/%m/%y")}'
    body = f"""Assalamu Alaikum {name},

MashAllah! Your Al Rawdha Matrimonial Profile has been successfully updated.

You can continue to your Profile ID and Profile Key for any future updates.

Attached is the updated profile PDF for your reference. Please review it to ensure all details are correct.

May Allah bless your efforts and guide you towards the right match.

Warm regards,
Al Rawdha Community Matrimonial Team
"""
    yag.send(to=to_email, subject=subject, contents=body, attachments=pdf_file)


