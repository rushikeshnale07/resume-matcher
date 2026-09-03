"""
Text extraction from uploaded resume files (PDF, DOCX, TXT).
"""
import io


def extract_text(uploaded_file) -> str:
    """
    uploaded_file: a Streamlit UploadedFile (has .name and behaves like a file).
    Returns plain extracted text.
    """
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        return _extract_pdf(uploaded_file)
    elif name.endswith(".docx"):
        return _extract_docx(uploaded_file)
    elif name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {name}. Please upload PDF, DOCX, or TXT.")


def _extract_pdf(uploaded_file) -> str:
    import pdfplumber

    text_parts = []
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_docx(uploaded_file) -> str:
    import docx

    doc = docx.Document(io.BytesIO(uploaded_file.read()))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
