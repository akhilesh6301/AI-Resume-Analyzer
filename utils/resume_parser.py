import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):

    text = ""

    document = fitz.open(pdf_path)

    for page in document:
        text += page.get_text()

    document.close()

    return text