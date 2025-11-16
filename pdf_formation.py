from fpdf import FPDF
import pandas as pd
from datetime import datetime
from fpdf.enums import XPos, YPos
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

# Google Drive Configuration
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")  # Optional: specific folder ID

# Al Rawdha Matrimony Color Scheme
PRIMARY_GREEN = (46, 84, 74)      # #2E544A - Deep Green
SECONDARY_SAND = (220, 203, 174)   # #DCCBAE - Sand
ACCENT_OLIVE = (122, 142, 107)     # #7A8E6B - Olive
HIGHLIGHT_CREAM = (248, 246, 240)  # #F8F6F0 - Cream

# Gender-based colors - Vibrant & Modern
FEMALE_PINK = (241, 98, 123)      # Rose Pink #E91E63
MALE_BLUE = (2, 119, 189)        # Ocean Blue #0277BD

def create_gender_buttons(values_str, pdf, gender):
    """Create gender-colored buttons for 'Open to matches from' field."""
    if not values_str or pd.isna(values_str):
        return

    # Split values by comma
    values = [v.strip() for v in str(values_str).split(',')]

    # Determine button color based on gender
    button_color = FEMALE_PINK if gender.lower() == 'female' else MALE_BLUE

    # Calculate total width needed for all buttons
    total_width = 0
    button_widths = []
    for value in values:
        tag_width = len(value) * 2.2 + 10  # Increased width for 10pt font
        button_widths.append(tag_width)
        total_width += tag_width + 3  # Add spacing
    total_width -= 3  # Remove last spacing

    # Calculate starting X position to center the buttons
    page_width = 210  # A4 width in mm
    start_x = (page_width - total_width) / 2
    start_y = pdf.get_y()
    x_position = start_x
    y_position = start_y

    for i, value in enumerate(values):
        tag_width = button_widths[i]

        # Calculate darker color for shadow
        shadow_color = tuple(max(0, int(c * 0.8)) for c in button_color)

        # Draw shadow (slightly offset and darker)
        pdf.set_fill_color(*shadow_color)
        pdf.set_line_width(0)
        pdf.rect(x_position + 0.5, y_position + 0.5, tag_width, 7, 'F', round_corners=True, corner_radius=1.5)

        # Draw rounded rectangle for button
        pdf.set_fill_color(*button_color)
        pdf.set_draw_color(*button_color)
        pdf.set_line_width(0.3)
        pdf.rect(x_position, y_position, tag_width, 7, 'DF', round_corners=True, corner_radius=1.5)

        # Draw button text
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(255, 255, 255)  # White text
        pdf.set_xy(x_position + 2, y_position + 1.5)
        pdf.cell(tag_width - 4, 4, value, align="C")

        x_position += tag_width + 3

    # Move cursor after buttons
    pdf.set_xy(20, y_position + 10)

def calculate_content_length(data):
    """Calculate total content length to determine appropriate font size."""
    total_chars = 0

    # Ethnicity and Residence
    if 'Nationality' in data and pd.notna(data['Nationality']):
        total_chars += len(str(data['Nationality']))
    if 'Ethnicity' in data and pd.notna(data['Ethnicity']):
        total_chars += len(str(data['Ethnicity']))
    if 'Residence' in data and pd.notna(data['Residence']):
        total_chars += len(str(data['Residence']))

    # Personal details
    for field in ['Age', 'Marriage Status', 'Children?', 'Height']:
        if field in data and pd.notna(data[field]):
            total_chars += len(str(data[field]))

    # Other sections
    for field in ['Dress', 'Islamic Scholars and Speakers', 'Work/Education', 'My Islam', 'Self Summary', "I'm looking for ..."]:
        if field in data and pd.notna(data[field]):
            total_chars += len(str(data[field]))

    # Preferred details
    for field in ['Open to matches from', 'Preferred Ethnic Background', 'Preferred Age Range']:
        if field in data and pd.notna(data[field]):
            total_chars += len(str(data[field]))

    return total_chars

def upload_to_drive(file_path, file_name):
    """Upload PDF to Google Drive and return shareable link."""
    try:
        # Authenticate with Google Drive API
        scope = ['https://www.googleapis.com/auth/drive.file']
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
        service = build('drive', 'v3', credentials=creds)

        # File metadata
        file_metadata = {
            'name': file_name,
            'mimeType': 'application/pdf'
        }

        # Add to specific folder if DRIVE_FOLDER_ID is set
        if DRIVE_FOLDER_ID:
            file_metadata['parents'] = [DRIVE_FOLDER_ID]

        # Upload file
        media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # Make file publicly viewable
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(
            fileId=file.get('id'),
            body=permission
        ).execute()

        # Return shareable link
        return file.get('webViewLink')

    except Exception as e:
        print(f"Warning: Failed to upload to Google Drive - {e}")
        return None

def create_pdf(data, user_id):
    """Create a single-page Al Rawdha Matrimony PDF profile with gender-based header."""
    pdf = FPDF()
    pdf.add_page()

    # Determine gender for header/text/button colors
    gender = data.get('Gender', 'Male')
    gender_color = FEMALE_PINK if str(gender).lower() == 'female' else MALE_BLUE

    # Set minimum font size to 10 points
    title_font = 12
    content_font = 10
    line_height = 4.5
    spacing = 2.5

    # Header Section with gender-specific background
    pdf.set_fill_color(*gender_color)
    pdf.rect(0, 0, 210, 40, 'F')

    # Title: Al Rawdha Matrimony (centered)
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_xy(0, 12)
    pdf.cell(210, 8, "Al Rawdha Matrimony", align="C")

    # Subheading: Profile ID (centered)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(0, 24)
    pdf.cell(210, 6, f"Profile ID: {user_id}", align="C")

    # Add logo above footer (will be placed later)
    logo_path = 'logo.jpg'

    # Start content area
    y_position = 48
    left_margin = 20
    content_width = 170

    # Section 1: Personal Details (Age, Marriage Status, Children, Height as buttons - directly below header, no subtitle)
    personal_details = []

    # Age - strip to number and add "years old"
    if 'Age' in data and pd.notna(data['Age']):
        age_str = str(data['Age']).strip()
        # Extract just the number
        age_num = ''.join(filter(str.isdigit, age_str))
        if age_num:
            personal_details.append(f"{age_num} years old")

    if 'Marriage Status' in data and pd.notna(data['Marriage Status']):
        personal_details.append(str(data['Marriage Status']))

    # Children - expand "No" to "No children", otherwise keep as is
    if 'Children?' in data and pd.notna(data['Children?']):
        children_str = str(data['Children?']).strip()
        if children_str.lower() == 'no':
            personal_details.append("No children")
        else:
            personal_details.append("Has child(ren)")

    if 'Height' in data and pd.notna(data['Height']):
        personal_details.append(str(data['Height']))

    if personal_details:
        pdf.set_xy(left_margin, y_position)
        create_gender_buttons(', '.join(personal_details), pdf, gender)
        y_position = pdf.get_y() + spacing

    # Helper function to add centered section
    def add_section(title, content_text, is_buttons=False):
        nonlocal y_position

        # Section title (centered, bold) - use gender color
        pdf.set_xy(left_margin, y_position)
        pdf.set_font("helvetica", "B", title_font)
        pdf.set_text_color(*gender_color)
        pdf.cell(content_width, 5, title, align="C")
        y_position += 5 + spacing

        # Content (centered)
        if is_buttons:
            # For button content, center the buttons
            pdf.set_xy(left_margin, y_position)
            create_gender_buttons(content_text, pdf, gender)
            y_position = pdf.get_y() + spacing
        else:
            pdf.set_xy(left_margin, y_position)
            pdf.set_font("helvetica", "", content_font)
            pdf.set_text_color(0, 0, 0)  # Black text for content

            # Encode for Latin-1 compatibility
            content_encoded = str(content_text).encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(content_width, line_height, content_encoded, align="C")
            y_position = pdf.get_y() + spacing

    # Section 2: Ethnicity and Residence
    ethnicity_parts = []
    if 'Nationality' in data and pd.notna(data['Nationality']):
        ethnicity_parts.append(str(data['Nationality']))
    if 'Ethnicity' in data and pd.notna(data['Ethnicity']):
        ethnicity_parts.append(str(data['Ethnicity']))
    if 'Residence' in data and pd.notna(data['Residence']):
        city = str(data['Residence'])
        ethnicity_parts.append(f"living in {city}")

    if ethnicity_parts:
        ethnicity_text = ', '.join(ethnicity_parts)
        add_section("Ethnicity and Residence", ethnicity_text)

    # Section 3: Self Summary
    if 'Self Summary' in data and pd.notna(data['Self Summary']):
        add_section("Self Summary", data['Self Summary'])

    # Section 4: Work and Education
    if 'Work/Education' in data and pd.notna(data['Work/Education']):
        add_section("Work and Education", data['Work/Education'])

    # Section 5: Dress
    if 'Dress' in data and pd.notna(data['Dress']):
        add_section("Dress", data['Dress'])

    # Section 6: My Islam
    if 'My Islam' in data and pd.notna(data['My Islam']):
        add_section("My Islam", data['My Islam'])

    # Section 7: Islamic Scholars and Speakers
    if 'Islamic Scholars and Speakers' in data and pd.notna(data['Islamic Scholars and Speakers']):
        add_section("Islamic Scholars and Speakers", data['Islamic Scholars and Speakers'])

    # Section 8: What I'm Looking For
    if "I'm looking for ..." in data and pd.notna(data["I'm looking for ..."]):
        add_section("What I'm Looking For", data["I'm looking for ..."])

    # Preferred Ethnic Background (with subtitle)
    if 'Preferred Ethnic Background' in data and pd.notna(data['Preferred Ethnic Background']) and str(data['Preferred Ethnic Background']).strip():
        add_section("Preferred Ethnic Background", data['Preferred Ethnic Background'])

    # Preferred Age Range (with subtitle)
    if 'Preferred Age Range' in data and pd.notna(data['Preferred Age Range']) and str(data['Preferred Age Range']).strip():
        add_section("Preferred Age Range", data['Preferred Age Range'])

    # Open To... (only specific options as buttons: Widows, Single Parents, Reverts, Divorcees)
    if 'Open to matches from' in data and pd.notna(data['Open to matches from']) and str(data['Open to matches from']).strip():
        open_to_str = str(data['Open to matches from'])
        # Check if it contains any of the specific keywords
        keywords = ['widows', 'single parents', 'reverts', 'divorcees', 'divorced']
        open_to_lower = open_to_str.lower()

        if any(keyword in open_to_lower for keyword in keywords):
            pdf.set_xy(left_margin, y_position)
            pdf.set_font("helvetica", "B", title_font)
            pdf.set_text_color(*gender_color)
            pdf.cell(content_width, 5, "Open To ...", align="C")
            y_position += 5 + spacing
            pdf.set_xy(left_margin, y_position)
            create_gender_buttons(open_to_str, pdf, gender)
            y_position = pdf.get_y() + spacing

    # Footer with representative contact (green color, larger font) - fixed at bottom of page 1
    if "Representative's Number" in data and pd.notna(data["Representative's Number"]):
        rep_number = str(data["Representative's Number"])

        # Disable auto page break temporarily
        pdf.set_auto_page_break(False)

        # Go to page 1 if we're on a different page
        if pdf.page_no() > 1:
            pdf.set_page(1)

        # Draw green footer background at bottom of page 1
        pdf.set_fill_color(*PRIMARY_GREEN)
        footer_height = 15
        footer_y = 297 - footer_height  # A4 height is 297mm
        pdf.rect(0, footer_y, 210, footer_height, 'F')

        # Add logo above the green footer
        if os.path.exists(logo_path):
            try:
                # Position logo above footer (footer starts at 282mm, logo is 25mm wide and proportional height)
                logo_y = footer_y - 30  # Place logo 30mm above footer
                pdf.image(logo_path, x=170, y=logo_y, w=25)
            except Exception as e:
                print(f"Warning: Could not add logo - {e}")

        # Add contact text in white - minimum 10 points
        pdf.set_xy(5, footer_y + 4)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(255, 255, 255)  # White text
        contact_text = f"Interested? Contact representative: {rep_number}"
        contact_encoded = contact_text.encode("latin-1", "replace").decode("latin-1")
        pdf.cell(200, 7, contact_encoded, align="C")

    # Save PDF
    filename = f'data/{user_id}_{datetime.now().strftime("%d_%m_%y")}.pdf'

    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    pdf.output(filename)

    return filename

# -----------------------------
# TESTING WORKFLOW
# -----------------------------
if __name__ == "__main__":
    testing = pd.read_csv('testing.csv')
    for i, row in testing.iterrows():
        try:
            user_id = row['Profile ID']

            create_pdf(row, user_id)

            print(f'Successfully created PDF for {user_id}_{datetime.now().strftime("%d_%m_%y")}.pdf')
        except Exception as e:
            print(f"Error creating PDF for {user_id}: {e}")


