import os
import yagmail
from dotenv import load_dotenv
from datetime import datetime

load_dotenv() 

# Gmail credentials for sending emails (can use App Password)
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # Replace with your app password

def intiation_email(to_email,name, user_id, pdf_file):
    """Send first-time profile creation email with PDF attachment"""
    yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)
    subject = f'🎉 Welcome to Al Rawdha! Your Matrimonial Profile is Ready {datetime.now().strftime("%d/%m/%y")}'
    
    body = f"""Assalamu Alaykum {name},

Your Al Rawdha Matrimonial Profile has been successfully created.

✨ Your unique Profile ID: {user_id}
You can use this ID anytime to update your profile in the future.

Attached is your profile PDF for your reference. Please review it and this will be sent on our AlRawdha Matrimonial WhatsApp Broadcast.

May Allah bless your efforts and guide you towards the right match.

Warm regards,
Al Rawdha Community Matchmaking
"""
    yag.send(to=to_email, subject=subject, contents=body, attachments=pdf_file)

def error_email(to_email, name, user_id, pdf_file):
    """
    Send an error email if the user entered an invalid Profile ID
    in the 'If updating, add Profile ID (from email)' field.
    """
    yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)
    subject = f'⚠️ Al Rawdha Matrimonial Profile Error {datetime.now().strftime("%d/%m/%y")}'
    body = f"""Assalamu Alaykum {name},

It looks like the Profile ID you entered in the 'If updating, add Profile ID (from email)' field
does not match any existing Al Rawdha Profile ID. 

If you want to make an amendment to your existing profile, please use the correct Profile ID
that was emailed to you when your first profile was created.

If you are creating a new profile, please leave 'If updating, add Profile ID (from email)' empty.

Warm regards,
Al Rawdha Community Matrimonal Team
"""
    yag.send(to=to_email, subject=subject, contents=body, attachments=pdf_file)

def ammendment_email(to_email,name, user_id, pdf_file):
    """Send email with ID and PDF attachment"""
    yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)
    subject = f'📝 Al Rawdha Profile Updated Successfully {datetime.now().strftime("%d/%m/%y")}'
    body = f"""Assalamu Alaikum {name},

MashAllah! Your Al Rawdha Matrimonial Profile has been successfully updated.

Your Profile ID: {user_id}
You can continue to use this ID for any future updates.

Attached is the updated profile PDF for your reference. Please review it to ensure all details are correct.

May Allah bless your efforts and guide you towards the right match.

Warm regards,
Al Rawdha Community Matrimonial Team
"""
    yag.send(to=to_email, subject=subject, contents=body, attachments=pdf_file)

    