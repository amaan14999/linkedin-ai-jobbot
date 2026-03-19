import os
from pypdf import PdfReader


def parse_resume_to_text(pdf_filename: str, output_filename: str = "resume.txt") -> str:
    """
    Reads a PDF, extracts its text, saves it to a .txt file, and returns the text.
    """
    pdf_path = os.path.join(os.getcwd(), pdf_filename)
    out_path = os.path.join(os.getcwd(), output_filename)

    # 1. Check if the PDF actually exists
    if not os.path.exists(pdf_path):
        print(f"[!] Could not find resume at '{pdf_path}'.")

        # Fallback: If the PDF is missing but the .txt file is already there, use it.
        if os.path.exists(out_path):
            print(f"[*] Falling back to existing '{output_filename}'.")
            with open(out_path, "r", encoding="utf-8") as f:
                return f.read()
        return "Resume not provided."

    # 2. Parse the PDF
    try:
        reader = PdfReader(pdf_path)
        text_chunks = []

        for page in reader.pages:
            # Extract text and drop excessive whitespace
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text.strip())

        final_text = "\n\n".join(text_chunks)

        # 3. Write it to resume.txt so you have a physical copy to verify
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(final_text)

        print(f"[*] Successfully parsed '{pdf_filename}' into '{output_filename}'.")
        return final_text

    except Exception as e:
        print(f"[!] Failed to parse PDF: {e}")
        return "Resume not provided."
