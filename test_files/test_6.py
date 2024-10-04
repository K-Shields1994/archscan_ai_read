import sys
import io
import math
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# Azure Form Recognizer endpoint and key
endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
key = "18ce006f0ac44579a36bfaf01653254c"

# File paths for the input PDF and output searchable PDF
input_file = 'C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P002.pdf'
output_file = 'C:/Users/liams/OneDrive/Desktop/Test_Data/Output_Folder/PGCPS-LF-03384_P002_ocr.pdf'


def calculate_word_rotation(polygon):
    """Calculate the rotation angle of the word based on its bounding box (polygon)."""
    dx = polygon[1].x - polygon[0].x
    dy = polygon[1].y - polygon[0].y
    angle = math.degrees(math.atan2(dy, dx))
    return angle


def main():
    print(f"Loading input file {input_file}")
    if not input_file.lower().endswith('.pdf'):
        sys.exit(f"Error: Unsupported input file extension {input_file}. Supported extension: PDF")

    print(f"Starting Azure Form Recognizer OCR process...")
    document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    with open(input_file, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=f)

    ocr_results = poller.result()
    print(f"OCR completed for {len(ocr_results.pages)} pages.")

    output = PdfWriter()
    default_font = "Times-Roman"
    confidence_threshold = 0.5  # Set a threshold for word confidence

    with open(input_file, "rb") as input_pdf_stream:
        original_pdf = PdfReader(input_pdf_stream)

        for page_id, page in enumerate(ocr_results.pages):
            ocr_overlay = io.BytesIO()

            original_page = original_pdf.pages[page_id]
            page_width = original_page.mediabox.width
            page_height = original_page.mediabox.height
            rotation = original_page.get('/Rotate', 0)

            x_scale = page_width / page.width
            y_scale = page_height / page.height
            scale = min(x_scale, y_scale)  # Use a uniform scale

            pdf_canvas = canvas.Canvas(ocr_overlay, pagesize=(page_width, page_height))

            if rotation != 0:
                pdf_canvas.translate(page_width / 2, page_height / 2)
                pdf_canvas.rotate(rotation)
                pdf_canvas.translate(-page_width / 2, -page_height / 2)

            for word in page.words:
                if word.confidence < confidence_threshold:
                    print(f"Skipping low-confidence word: {word.content} (Confidence: {word.confidence})")
                    continue  # Skip low-confidence words

                word_width = word.polygon[1].x - word.polygon[0].x
                word_height = word.polygon[3].y - word.polygon[0].y
                font_size = word_height * scale

                x_position = word.polygon[0].x * scale
                y_position = page_height - word.polygon[0].y * scale

                word_rotation = calculate_word_rotation(word.polygon)
                print(f"Word: {word.content}, Rotation: {word_rotation:.2f} degrees, X: {x_position:.2f}, Y: {y_position:.2f}")

                pdf_canvas.saveState()
                pdf_canvas.translate(x_position, y_position)
                pdf_canvas.rotate(word_rotation)
                pdf_canvas.setFont(default_font, font_size)
                pdf_canvas.setFillColorRGB(1, 1, 1, alpha=0)  # Invisible text
                pdf_canvas.drawString(0, 0, word.content)
                pdf_canvas.restoreState()

            pdf_canvas.save()
            ocr_overlay.seek(0)

            new_pdf_page = PdfReader(ocr_overlay)
            original_page.merge_page(new_pdf_page.pages[0])

            output.add_page(original_page)

    with open(output_file, "wb") as outputStream:
        output.write(outputStream)

    print(f"Searchable PDF created: {output_file}")


if __name__ == '__main__':
    main()
