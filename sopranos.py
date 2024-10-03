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
input_file = '/Volumes/SSD/pg_hs/1_test/PGCPS-LF-03384/PGCPS-LF-03384_P001.pdf'
output_file = '/Volumes/SSD/pg_hs/1_test/PGCPS-LF-03384/PGCPS-LF-03384_P001_ocr.pdf'


def main():
    # Loading input file
    print(f"Loading input file {input_file}")
    if not input_file.lower().endswith('.pdf'):
        sys.exit(f"Error: Unsupported input file extension {input_file}. Supported extension: PDF")

    # Running OCR using Azure Form Recognizer Read API
    print(f"Starting Azure Form Recognizer OCR process...")
    document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    with open(input_file, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=f)

    ocr_results = poller.result()
    print(f"Azure Form Recognizer finished OCR text for {len(ocr_results.pages)} pages.")

    # Generate OCR overlay layer for the searchable PDF
    print(f"Generating searchable PDF...")
    output = PdfWriter()
    default_font = "Times-Roman"

    # Open original PDF to use as a background
    with open(input_file, "rb") as input_pdf_stream:
        original_pdf = PdfReader(input_pdf_stream)

        for page_id, page in enumerate(ocr_results.pages):
            ocr_overlay = io.BytesIO()

            # Get original page dimensions
            original_page = original_pdf.pages[page_id]
            page_width = original_page.mediabox.width
            page_height = original_page.mediabox.height

            # Adjust scaling factor based on PDF and OCR coordinates
            scale = (page_width / page.width + page_height / page.height) / 2.0
            pdf_canvas = canvas.Canvas(ocr_overlay, pagesize=(page_width, page_height))

            text = pdf_canvas.beginText()
            text.setTextRenderMode(3)  # Set text rendering mode to invisible

            # Loop through each word in OCR results
            for word in page.words:
                word_width = word.polygon[1].x - word.polygon[0].x
                word_height = word.polygon[3].y - word.polygon[0].y
                font_size = word_height * scale

                # Calculate text position (adjust for PDF's flipped y-axis)
                x_position = word.polygon[0].x * scale
                y_position = page_height - word.polygon[0].y * scale

                # Calculate rotation angle and apply 180-degree correction
                dx = word.polygon[1].x - word.polygon[0].x
                dy = word.polygon[1].y - word.polygon[0].y
                text_angle = math.atan2(dy, dx) + math.pi  # Rotate by 180 degrees

                text.setFont(default_font, font_size)
                text.setTextTransform(
                    math.cos(text_angle), -math.sin(text_angle),
                    math.sin(text_angle), math.cos(text_angle),
                    x_position, y_position
                )

                # Render the invisible text
                text.textOut(word.content + " ")

            pdf_canvas.drawText(text)
            pdf_canvas.save()

            ocr_overlay.seek(0)

            # Merge OCR overlay with the original page
            new_pdf_page = PdfReader(ocr_overlay)
            original_page.merge_page(new_pdf_page.pages[0])

            output.add_page(original_page)

    # Save the final searchable PDF
    with open(output_file, "wb") as outputStream:
        output.write(outputStream)

    print(f"Searchable PDF created: {output_file}")


# Run the script
if __name__ == '__main__':
    main()