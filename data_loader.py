from docx import Document
from langchain_community.document_loaders import PyMuPDFLoader


def load_resume(file_path):
    """
    Lädt den Inhalt einer Lebenslauf-Datei.

    Parameter:
    file (str): Der Pfad zur Lebenslauf-Datei.

    Rückgabe:
    str: Der Inhalt der Lebenslauf-Datei.
    """
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    page_content = ""
    for page in pages:
        page_content += page.page_content
    return page_content


def write_cover_letter_to_doc(text, filename="temp/cover_letter.docx"):
    """
    Schreibt den gegebenen Text als Anschreiben in ein Word-Dokument.

    Parameter:
    text (str): Der Textinhalt des Anschreibens.
    filename (str): Der Dateiname und Pfad, unter dem das Dokument gespeichert wird. Standard ist "temp/cover_letter.docx".

    Rückgabe:
    str: Der Dateiname und Pfad des gespeicherten Dokuments.
    """
    doc = Document()
    paragraphs = text.split("\n")
    # Füge jeden Absatz zum Dokument hinzu
    for para in paragraphs:
        doc.add_paragraph(para)
    # Speichere das Dokument in der angegebenen Datei
    doc.save(filename)
    return filename
