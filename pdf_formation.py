from fpdf import FPDF
import pandas as pd
from datetime import datetime
from fpdf.enums import XPos, YPos
import os

# Al Rawdha Matrimony Color Scheme
PRIMARY_GREEN = (46, 84, 74)      # #2E544A - Deep Green
SECONDARY_SAND = (220, 203, 174)   # #DCCBAE - Sand
ACCENT_OLIVE = (122, 142, 107)     # #7A8E6B - Olive
HIGHLIGHT_CREAM = (248, 246, 240)  # #F8F6F0 - Cream

# Gender-based colors - Vibrant & Modern
FEMALE_PINK = (241, 98, 123)      # Rose Pink #E91E63
MALE_BLUE = (2, 119, 189)        # Ocean Blue #0277BD

def calculate_age(dob_str):
    """Calculate age from date of birth string."""
    if not dob_str or pd.isna(dob_str):
        return None

    try:
        # Try different date formats
        for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y']:
            try:
                dob = datetime.strptime(str(dob_str).strip(), fmt)
                today = datetime.now()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                return age
            except ValueError:
                continue
        return None
    except:
        return None

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
        tag_width = len(value) * 1.8 + 10
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
        pdf.set_font("helvetica", "B", 8)
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
    if 'Nationality / Immigration Status' in data and pd.notna(data['Nationality / Immigration Status']):
        total_chars += len(str(data['Nationality / Immigration Status']))
    if 'Ethnic Background' in data and pd.notna(data['Ethnic Background']):
        total_chars += len(str(data['Ethnic Background']))
    if 'City of Residence' in data and pd.notna(data['City of Residence']):
        total_chars += len(str(data['City of Residence']))

    # Age and Height
    if 'Height' in data and pd.notna(data['Height']):
        total_chars += len(str(data['Height']))

    # Other sections
    for field in ['Work and Education', 'My Islam (in detail)', 'Self Summary', "I'm looking for ..."]:
        if field in data and pd.notna(data[field]):
            total_chars += len(str(data[field]))

    if 'Open to matches from' in data and pd.notna(data['Open to matches from']):
        total_chars += len(str(data['Open to matches from']))

    return total_chars

def create_pdf(data, user_id):
    """Create a single-page Al Rawdha Matrimony PDF profile with gender-based header."""
    pdf = FPDF()
    pdf.add_page()

    # Determine gender for header/text/button colors
    gender = data.get('Gender', 'Male')
    gender_color = FEMALE_PINK if str(gender).lower() == 'female' else MALE_BLUE

    # Calculate dynamic font sizes based on content length
    content_length = calculate_content_length(data)

    # Adjust font sizes based on content (more content = smaller fonts)
    if content_length < 500:
        title_font = 10
        content_font = 9
        line_height = 4
        spacing = 2
    elif content_length < 800:
        title_font = 9
        content_font = 8
        line_height = 3.5
        spacing = 1.5
    elif content_length < 1200:
        title_font = 8
        content_font = 7
        line_height = 3
        spacing = 1
    else:
        title_font = 7
        content_font = 6.5
        line_height = 2.5
        spacing = 0.5

    # Header Section with gender-specific background
    pdf.set_fill_color(*gender_color)
    pdf.rect(0, 0, 210, 40, 'F')

    # Title: Al Rawdha Matrimony (centered)
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_xy(0, 12)
    pdf.cell(210, 8, "Al Rawdha Matrimony", align="C")

    # Subheading: Profile ID (centered)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(0, 24)
    pdf.cell(210, 6, f"Profile ID: {user_id}", align="C")

    # Add logo in bottom right corner
    logo_path = 'logo.jpg'
    if os.path.exists(logo_path):
        try:
            # Position logo in bottom right (A4 = 297mm height, 210mm width)
            pdf.image(logo_path, x=170, y=267, w=25)
        except Exception as e:
            print(f"Warning: Could not add logo - {e}")

    # Start content area
    y_position = 48
    left_margin = 20
    content_width = 170

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

    # Section 1: Ethnicity and Residence
    ethnicity_parts = []
    if 'Nationality / Immigration Status' in data and pd.notna(data['Nationality / Immigration Status']):
        ethnicity_parts.append(str(data['Nationality / Immigration Status']))
    if 'Ethnic Background' in data and pd.notna(data['Ethnic Background']):
        ethnicity_parts.append(str(data['Ethnic Background']))
    if 'City of Residence' in data and pd.notna(data['City of Residence']):
        city = str(data['City of Residence'])
        ethnicity_parts.append(f"living in {city}")

    if ethnicity_parts:
        ethnicity_text = ', '.join(ethnicity_parts)
        add_section("Ethnicity and Residence", ethnicity_text)

    # Section 2: Age and Height
    age_height_parts = []
    if 'Date of Birth' in data:
        age = calculate_age(data['Date of Birth'])
        if age:
            age_height_parts.append(f"{age} years old")
    if 'Height' in data and pd.notna(data['Height']):
        age_height_parts.append(str(data['Height']))

    if age_height_parts:
        age_height_text = ', '.join(age_height_parts)
        add_section("Age and Height", age_height_text)

    # Section 3: Work and Education
    if 'Work and Education' in data and pd.notna(data['Work and Education']):
        add_section("Work and Education", data['Work and Education'])

    # Section 4: My Islam
    if 'My Islam (in detail)' in data and pd.notna(data['My Islam (in detail)']):
        add_section("My Islam", data['My Islam (in detail)'])

    # Section 5: Self Summary
    if 'Self Summary' in data and pd.notna(data['Self Summary']):
        add_section("Self Summary", data['Self Summary'])

    # Section 6: What I'm Looking For
    if "I'm looking for ..." in data and pd.notna(data["I'm looking for ..."]):
        add_section("What I'm Looking For", data["I'm looking for ..."])

    # Section 7: Open To (only if exists and has value)
    if 'Open to matches from' in data and pd.notna(data['Open to matches from']) and str(data['Open to matches from']).strip():
        pdf.set_xy(left_margin, y_position)
        pdf.set_font("helvetica", "B", title_font)
        pdf.set_text_color(*gender_color)
        pdf.cell(content_width, 5, "Open To ...", align="C")
        y_position += 5 + spacing
        pdf.set_xy(left_margin, y_position)
        create_gender_buttons(data['Open to matches from'], pdf, gender)
        y_position = pdf.get_y()

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
    testing = pd.read_csv('female_testing.csv')
    for i, row in testing.iterrows():
        try:
            user_id = row['Profile ID']

            create_pdf(row, user_id)

            print(f'Successfully created PDF for {user_id}_{datetime.now().strftime("%d_%m_%y")}.pdf')
        except Exception as e:
            print(f"Error creating PDF for {user_id}: {e}")


