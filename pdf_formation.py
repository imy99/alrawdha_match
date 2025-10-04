from fpdf import FPDF
import tempfile
import pandas as pd
from datetime import datetime
from fpdf.enums import XPos, YPos

def create_pdf(data, user_id):
    """Create a professional PDF profile using built-in fonts."""
    pdf = FPDF()
    pdf.add_page()
    
    # Header section with subtle background
    pdf.set_fill_color(248, 249, 250)  # Very light gray background
    pdf.rect(10, 10, 190, 30, 'F')  # Header background rectangle
    
    # Title
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(44, 62, 80)  # Dark blue-gray
    pdf.set_xy(10, 20)
    pdf.cell(190, 10, f"Dating Profile ID: {user_id}", align="C")
    
    # Timestamp
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(108, 117, 125)  # Gray
    pdf.set_xy(10, 32)
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.cell(190, 8, f"Generated: {timestamp}", align="C")
    
    pdf.ln(25)
    
    # Reset text color for content
    pdf.set_text_color(33, 37, 41)  # Dark gray
    
    # Define sections
    sections = {
        "Personal Information": ["Profile ID", "Full Name (will be kept anonymous)", "Gender", "Date of Birth", "Ethnic Background"],
        "Contact Information": ["Email", "Phone number (will be kept anonymous)"],
        "Location & Status": ["City of Residence", "Nationality / Immigration Status"]
    }
    
    y_position = pdf.get_y() + 10
    
    for section_title, fields in sections.items():
        # Section header
        pdf.set_xy(10, y_position)
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(52, 73, 94)  # Darker blue-gray
        pdf.cell(0, 12, section_title)
        y_position += 18
        
        # Section content box
        section_height = len([field for field in fields if field in data]) * 15 + 10
        pdf.set_fill_color(253, 253, 253)  # Very light gray
        pdf.rect(15, y_position - 5, 180, section_height, 'F')
        
        # Draw left border for section
        pdf.set_draw_color(108, 117, 125)
        pdf.set_line_width(2)
        pdf.line(15, y_position - 5, 15, y_position - 5 + section_height)
        
        # Section fields
        for field in fields:
            if field in data and pd.notna(data[field]) and str(data[field]).strip() != '':
                pdf.set_xy(25, y_position)
                
                # Field label
                pdf.set_font("helvetica", "B", 11)
                pdf.set_text_color(73, 80, 87)  # Medium gray
                
                # Clean up field names
                display_field = field.replace("(will be kept anonymous)", "").strip()
                pdf.cell(60, 10, f"{display_field}:")
                
                # Field value
                pdf.set_font("helvetica", "", 11)
                pdf.set_text_color(33, 37, 41)  # Dark gray
                
                value_str = str(data[field]).encode("latin-1", "replace").decode("latin-1")
                # Handle long text
                if len(value_str) > 40:
                    pdf.set_xy(90, y_position)
                    pdf.multi_cell(100, 10, value_str)
                    y_position += max(10, (len(value_str) // 40) * 10)
                else:
                    pdf.set_xy(90, y_position)
                    pdf.cell(100, 10, value_str)
                
                # Add privacy indicator for sensitive fields
                if "anonymous" in field.lower():
                    pdf.set_font("helvetica", "", 8)
                    pdf.set_text_color(40, 167, 69)  # Green
                    pdf.set_xy(90, y_position + 8)
                    pdf.cell(50, 6, "Protected", align="L")
                
                y_position += 15
        
        y_position += 20  # Space between sections
    
    # Footer section
    pdf.set_y(-50)  # Position from bottom
    
    # Footer background
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(10, pdf.get_y() - 5, 190, 35, 'F')
    
    # Footer text
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(108, 117, 125)
    pdf.multi_cell(
        0, 6,
        "This profile is shared anonymously with Al Rawdha community for matchmaking.\n"
        "Your personal information is protected and will remain confidential.\n"
        "To update your profile, use your Profile ID from the email.",
        align="C"
    )
    
    # Status indicator
    pdf.set_xy(10, pdf.get_y() + 5)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(40, 167, 69)
    pdf.cell(0, 6, " Profile Active", align="C")
    
    # Save PDF
    filename = f'data/{user_id}_{datetime.now().strftime("%d_%m_%y")}.pdf'
    pdf.output(filename)
    return filename

# Alternative version with even cleaner, minimal design
def create_minimal_pdf(data, user_id):
    """Create a minimal, clean PDF profile."""
    pdf = FPDF()
    pdf.add_page()
    
    # Simple header
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 15, f"Dating Profile ID: {user_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(5)
    
    # Timestamp
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(108, 117, 125)
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.cell(0, 10, timestamp, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)
    
    # Separator line
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(15)
    
    # Profile details with clean layout
    pdf.set_text_color(33, 37, 41)
    
    # Define section categories for better organization
    personal_fields = ["Profile ID", "Full Name", "Gender", "Date of Birth", "Ethnic Background"]
    contact_fields = ["Email", "Phone number"]
    location_fields = ["City of Residence", "Nationality", "Immigration Status"]
    islamic_fields = ["My Islam", "Islamic Scholars", "Dress"]
    lifestyle_fields = ["Self Summary", "Work and Education", "Hobbies", "Family"]
    preferences_fields = ["Preferred Ethnic Background", "I'm looking for", "Preferred Age Range", "Open to matches from"]
    representative_fields = ["Representative's Full Name", "Representative's Number", "Representative's Email"]
    
    # Track current section for dividers
    current_section = None
    
    for key, value in data.items():
        if pd.notna(value) and str(value).strip() != '':
            # Determine which section this field belongs to
            field_section = None
            if any(field in key for field in personal_fields):
                field_section = "Personal Information"
            elif any(field in key for field in contact_fields):
                field_section = "Contact Information"
            elif any(field in key for field in location_fields):
                field_section = "Location & Status"
            elif any(field in key for field in islamic_fields):
                field_section = "Islamic Practice"
            elif any(field in key for field in lifestyle_fields):
                field_section = "Lifestyle & Background"
            elif any(field in key for field in preferences_fields):
                field_section = "Preferences"
            elif any(field in key for field in representative_fields):
                field_section = "Representative Information"
            
            # Add section divider if we've moved to a new section
            if field_section and field_section != current_section:
                if current_section is not None:  # Don't add divider before first section
                    # Add subtle divider
                    pdf.ln(8)
                    pdf.set_draw_color(220, 220, 220)
                    pdf.set_line_width(0.3)
                    pdf.line(30, pdf.get_y(), 180, pdf.get_y())
                    pdf.ln(8)
                current_section = field_section
            
            # Label
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(73, 80, 87)
            clean_key = key.replace("(will be kept anonymous)", "").strip()
            pdf.cell(60, 12, f"{clean_key}:")
            
            # Value - use multi_cell for proper text wrapping
            pdf.set_font("helvetica", "", 11)
            pdf.set_text_color(33, 37, 41)
            value_str = str(value).encode("latin-1", "replace").decode("latin-1")
            
            # Get current position and calculate available width
            current_x = pdf.get_x()
            current_y = pdf.get_y()
            available_width = 190 - current_x  # Page width minus current x position
            
            # Use multi_cell for text wrapping
            pdf.multi_cell(available_width, 8, value_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Add subtle separator
            if "anonymous" in key.lower():
                pdf.set_font("helvetica", "", 8)
                pdf.set_text_color(134, 142, 150)
                pdf.cell(0, 6, "   (Protected)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            pdf.ln(3)
    
    # Footer
    pdf.ln(10)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(25, pdf.get_y(), 185, pdf.get_y())  # Adjusted for margins
    pdf.ln(10)
    
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(108, 117, 125)
    pdf.multi_cell(
        0, 6,
        "This profile is shared confidentially with Al Rawdha community for matchmaking purposes.\n"
        "To update your information, please use your Profile ID.",
        align="C"
    )
    
    # Save PDF
    filename = f'data/{user_id}_minimal_{datetime.now().strftime("%d_%m_%y")}.pdf'
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
            
            # Choose which version to use:
            # create_pdf(row, user_id)          # Structured version
            create_minimal_pdf(row, user_id)    # Minimal version
            
            print(f'✅ Successfully created PDF for {user_id}_{datetime.now().strftime("%d_%m_%y")}.pdf')
        except Exception as e:
            print(f"❌ Error creating PDF for {user_id}: {e}")


