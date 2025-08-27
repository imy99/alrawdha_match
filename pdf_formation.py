from fpdf import FPDF

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
    filename = f"data/profile_{user_id}.pdf"
    pdf.output(filename)

    return filename