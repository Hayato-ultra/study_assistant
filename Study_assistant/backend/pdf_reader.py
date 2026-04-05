import pdfplumber

def read_pdf(path):
    text=""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text+=page.extract_text() or ""
    return text