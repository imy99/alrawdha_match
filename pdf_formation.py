from fpdf import FPDF

def create_pdf(data, user_id):
    """Create a professional PDF profile using built-in fonts."""
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 15, f"Dating Profile ID: {user_id}", ln=True, align="C")
    pdf.ln(10)

    # Profile details
    pdf.set_font("Arial", "", 12)
    for key, value in data.items():
        value_str = str(value).encode("latin-1", "replace").decode("latin-1")  # replace unsupported chars
        pdf.set_font("Arial", "B", 12)
        pdf.cell(50, 10, f"{key}:", ln=0)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, value_str)
        pdf.ln(2)

    # Line separator
    pdf.ln(5)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    # Footer
    pdf.ln(5)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(
        0, 10,
        "This profile is shared anonymously with Al Rawdha community for matchmaking.\n"
        "If you wish to amend your profile, use your Profile ID from the email.",
        align="C"
    )

    # Save PDF
    filename = f"data/profile_{user_id}.pdf"
    pdf.output(filename)
    return filename
