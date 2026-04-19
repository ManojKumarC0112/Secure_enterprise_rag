import os
from fpdf import FPDF

files = [
    {"path": "data/public_handbook.pdf", "role": "Employee", "text": "This is the public employee handbook. Working hours are 9 to 5. Casual dress code on Fridays."},
    {"path": "data/product_roadmap.pdf", "role": "Manager", "text": "Here is the Q3 Product Roadmap. We are building an AI chatbot integrating external CRM systems."},
    {"path": "data/salary_structure.pdf", "role": "Admin", "text": "Confidential Salary Structure 2026. L1: $50,000. L2: $75,000. L3: $110,000. L4: $160,000+"}
]

os.makedirs("data", exist_ok=True)

for item in files:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Document Role: {item['role']}", ln=True, align='L')
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=item["text"])
    pdf.output(item["path"])

print("✅ Generated mock PDFs.")
