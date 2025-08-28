from fpdf import FPDF
import pandas as pd
from datetime import datetime
from fpdf.enums import XPos, YPos

def create_pdf(data, user_id):
    """Create a professional PDF profile using built-in fonts."""
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 15, f"Dating Profile ID: {user_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)

    # Profile details
    pdf.set_font("helvetica", "", 12)
    for key, value in data.items():
        value_str = str(value).encode("latin-1", "replace").decode("latin-1")  # replace unsupported chars
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(50, 10, f"{key}:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", "", 12)
        pdf.multi_cell(0, 10, value_str)
        pdf.ln(2)

    # Line separator
    pdf.ln(5)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    # Footer
    pdf.ln(5)
    pdf.set_font("helvetica", "I", 10)
    pdf.multi_cell(
        0, 10,
        "This profile is shared anonymously with Al Rawdha community for matchmaking.\n"
        "If you wish to amend your profile, use your Profile ID from the email.",
        align="C"
    )

    # Save PDF
    filename = f'data/{user_id}_{datetime.now().strftime("%d_%m_%y")}.pdf'
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
            print(f'✅ Successfully created PDF for {user_id}_{datetime.now().strftime("%d_%m_%y")}.pdf')
        except Exception as e:
            print(f"❌ Error creating PDF for {user_id}: {e}")


