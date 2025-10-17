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

def create_gradient_tags(values_str, pdf):
    """Create color-coded tags for 'Open to matches from' field with gradient colors."""
    if not values_str or pd.isna(values_str):
        return

    # Split values by comma
    values = [v.strip() for v in str(values_str).split(',')]

    # Define gradient colors (from Deep Green to Olive)
    gradient_colors = [
        (46, 84, 74),      # Deep Green
        (65, 100, 85),     # Transitional
        (84, 116, 96),     # Transitional
        (103, 129, 101),   # Transitional
        (122, 142, 107)    # Olive
    ]

    start_x = pdf.get_x()
    start_y = pdf.get_y()
    x_position = start_x
    y_position = start_y
    max_width = 170  # Maximum width before wrapping

    for i, value in enumerate(values):
        # Select color from gradient based on index
        color_index = min(i, len(gradient_colors) - 1)
        color = gradient_colors[color_index]

        # Calculate darker color for shadow
        shadow_color = tuple(max(0, c - 25) for c in color)

        # Estimate tag width (rough calculation)
        tag_width = len(value) * 2 + 8

        # Check if we need to wrap to next line
        if x_position + tag_width > start_x + max_width:
            x_position = start_x
            y_position += 11

        # Draw shadow (slightly offset and darker)
        pdf.set_fill_color(*shadow_color)
        pdf.set_line_width(0)
        pdf.rect(x_position + 0.5, y_position + 0.5, tag_width, 7, 'F', round_corners=True, corner_radius=1.5)

        # Draw rounded rectangle for tag
        pdf.set_fill_color(*color)
        pdf.set_draw_color(*color)
        pdf.set_line_width(0.3)
        pdf.rect(x_position, y_position, tag_width, 7, 'DF', round_corners=True, corner_radius=1.5)

        # Draw tag text
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(255, 255, 255)  # White text
        pdf.set_xy(x_position + 2, y_position + 1)
        pdf.cell(tag_width - 4, 5, value, align="C")

        x_position += tag_width + 4

    # Move cursor after tags
    pdf.set_xy(start_x, y_position + 13)

def create_pdf(data, user_id):
    """Create a professional Al Rawdha Matrimony PDF profile."""
    pdf = FPDF()
    pdf.add_page()

    # Header Section with Deep Green background
    pdf.set_fill_color(*PRIMARY_GREEN)
    pdf.rect(0, 0, 210, 50, 'F')

    # Title: Al Rawdha Matrimony
    pdf.set_font("helvetica", "B", 24)
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_xy(15, 18)
    pdf.cell(130, 12, "Al Rawdha Matrimony", align="L")

    # Subheading: Profile ID
    pdf.set_font("helvetica", "", 14)
    pdf.set_text_color(*HIGHLIGHT_CREAM)
    pdf.set_xy(15, 32)
    pdf.cell(130, 8, f"Profile ID: {user_id}", align="L")

    # Add logo in top right corner AFTER header background (so it's visible)
    logo_path = 'logo.jpg'
    if os.path.exists(logo_path):
        try:
            # Position logo in top right with better sizing
            pdf.image(logo_path, x=155, y=10, w=40)
        except Exception as e:
            print(f"Warning: Could not add logo - {e}")

    # Start content area
    pdf.set_y(60)

    # Define question order and display (ONLY public matchmaking information)
    # Excluded: Private/anonymous info (name, contact details, timestamps, representative info)
    questions = [
        ("Self Summary", "Self Summary"),
        ("Marriage Status", "Marriage Status"),
        ("Do you have children?", "Do you have children?"),
        ("Dress", "Dress"),
        ("Islamic Scholars and Speakers", "Islamic Scholars and Speakers"),
        ("Work and Education", "Work and Education"),
        ("Hobbies, Family and Lifestyle", "Hobbies, Family and Lifestyle"),
        ("My Islam (in detail)", "My Islam"),
        ("Ethnic Background", "Ethnic Background"),
        ("City of Residence", "City of Residence"),
        ("Nationality / Immigration Status", "Nationality / Immigration Status"),
        ("Height", "Height"),
        ("__SECTION__", "Preferences & Compatibility Details"),  # Section divider
        ("Preferred Ethnic Background", "Preferred Ethnic Background"),
        ("I'm looking for ...", "I'm looking for"),
        ("Preferred Age Range", "Preferred Age Range"),
        ("Open to matches from", "Open to matches from")
    ]

    # Set initial position
    y_position = 65
    left_margin = 25

    for field_key, display_name in questions:
        # Handle section dividers
        if field_key == "__SECTION__":
            # Check if we have enough space for the section (need at least 60mm for section + some content)
            if y_position > 187:  # 247mm - 60mm needed space
                # Start new page for Preferences section
                pdf.add_page()

                # Add header to new page
                pdf.set_fill_color(*PRIMARY_GREEN)
                pdf.rect(0, 0, 210, 50, 'F')

                # Add logo on new page
                if os.path.exists('logo.jpg'):
                    try:
                        pdf.image('logo.jpg', x=155, y=10, w=40)
                    except:
                        pass

                pdf.set_font("helvetica", "B", 16)
                pdf.set_text_color(255, 255, 255)
                pdf.set_xy(15, 20)
                pdf.cell(130, 10, f"Profile ID: {user_id}", align="L")

                y_position = 65
            else:
                # Add extra spacing before section on same page
                y_position += 20

            # Draw section subtitle
            pdf.set_xy(left_margin, y_position)
            pdf.set_font("helvetica", "B", 18)
            pdf.set_text_color(*PRIMARY_GREEN)
            pdf.cell(0, 10, display_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Add decorative line under subtitle
            y_position += 10
            pdf.set_draw_color(*ACCENT_OLIVE)
            pdf.set_line_width(1)
            pdf.line(left_margin, y_position, 185, y_position)
            y_position += 15
            continue

        # Check if field exists and has value
        if field_key in data and pd.notna(data[field_key]) and str(data[field_key]).strip() != '':
            value = str(data[field_key]).strip()

            # Estimate space needed for this field (question + answer + spacing)
            # Rough estimate: 8 (question) + estimated answer height + 10 (spacing) + 5 (separator)
            estimated_lines = max(1, len(str(value)) // 95)  # Approximate lines for answer
            estimated_height = 8 + (estimated_lines * 6) + 15

            # Check if we need a new page (leave 50mm for footer)
            if y_position + estimated_height > 247:  # 297mm page - 50mm footer space
                pdf.add_page()
                # Add header to new page
                pdf.set_fill_color(*PRIMARY_GREEN)
                pdf.rect(0, 0, 210, 50, 'F')
                pdf.set_font("helvetica", "B", 16)
                pdf.set_text_color(255, 255, 255)
                pdf.set_xy(15, 20)
                pdf.cell(130, 10, f"Profile ID: {user_id} (continued)", align="L")
                y_position = 60

            # Question Label (Bold, larger, Deep Green)
            pdf.set_xy(left_margin, y_position)
            pdf.set_font("helvetica", "B", 13)
            pdf.set_text_color(*PRIMARY_GREEN)

            # Clean display name (remove anonymous tags for display)
            clean_display = display_name.replace("(will be kept anonymous)", "").strip()
            pdf.cell(0, 8, clean_display, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            y_position += 8

            # Special handling for "Open to matches from" with gradient tags
            if field_key == "Open to matches from":
                pdf.set_xy(left_margin + 5, y_position)
                create_gradient_tags(value, pdf)
                y_position = pdf.get_y() + 8
            else:
                # Answer (Regular, Olive color)
                pdf.set_xy(left_margin + 5, y_position)
                pdf.set_font("helvetica", "", 11)
                pdf.set_text_color(*ACCENT_OLIVE)

                # Use multi_cell for text wrapping with proper width
                available_width = 160

                # Encode for Latin-1 compatibility
                value_encoded = value.encode("latin-1", "replace").decode("latin-1")

                # Calculate approximate height needed
                lines_needed = len(value_encoded) // 60 + 1

                pdf.multi_cell(available_width, 6, value_encoded, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                # Update y_position based on actual content height
                y_position = pdf.get_y() + 2

            # Add spacing between questions
            y_position += 10

            # Draw subtle separator line (Sand color)
            pdf.set_draw_color(*SECONDARY_SAND)
            pdf.set_line_width(0.5)
            pdf.line(left_margin, y_position - 5, 185, y_position - 5)

    # Footer Section
    pdf.set_y(-35)

    # Footer background (Sand color)
    pdf.set_fill_color(*SECONDARY_SAND)
    pdf.rect(0, pdf.get_y() - 5, 210, 40, 'F')

    # Footer text
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(*PRIMARY_GREEN)
    pdf.set_xy(20, pdf.get_y())
    pdf.multi_cell(
        170, 5,
        "This profile is shared confidentially with the Al Rawdha Matrimony community.\n"
        "All personal information is protected and will remain anonymous until mutual consent.\n"
        "To update your profile, please use your Profile ID provided in the email.",
        align="C"
    )


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


