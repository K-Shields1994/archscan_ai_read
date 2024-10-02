# Script to create searchable PDF from scan PDF or images using Azure Form Recognizer
# Required packages
# pip install --upgrade azure-ai-formrecognizer>=3.3 pypdf>=3.0 reportlab

import sys
import io
import math
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# Azure Form Recognizer endpoint and key
endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
key = "18ce006f0ac44579a36bfaf01653254c"

# Hardcoded input and output paths
input_file = '/Volumes/SSD/pg_hs/1_test/PGCPS-LF-03384/PGCPS-LF-03384_P001.pdf'
output_file = '/Volumes/SSD/pg_hs/1_test/PGCPS-LF-03384/PGCPS-LF-03384_P001_ocr.pdf'

def dist(p1, p2):
    return math.sqrt((p1.x - p2.x) * (p1.x - p2.x) + (p1.y - p2.y) * (p1.y - p2.y))

# Main function to run OCR and create searchable PDF
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

            scale = (page_width / page.width + page_height / page.height) / 2.0
            pdf_canvas = canvas.Canvas(ocr_overlay, pagesize=(page_width, page_height))

            text = pdf_canvas.beginText()
            # Set text rendering mode to invisible
            text.setTextRenderMode(3)
            for word in page.words:
                # Calculate optimal font size
                desired_text_width = max(dist(word.polygon[0], word.polygon[1]),
                                         dist(word.polygon[3], word.polygon[2])) * scale
                desired_text_height = max(dist(word.polygon[1], word.polygon[2]),
                                          dist(word.polygon[0], word.polygon[3])) * scale
                font_size = desired_text_height
                actual_text_width = pdf_canvas.stringWidth(word.content, default_font, font_size)

                # Calculate text rotation angle
                text_angle = math.atan2(
                    (word.polygon[1].y - word.polygon[0].y + word.polygon[2].y - word.polygon[3].y) / 2.0,
                    (word.polygon[1].x - word.polygon[0].x + word.polygon[2].x - word.polygon[3].x) / 2.0)
                text.setFont(default_font, font_size)
                text.setTextTransform(math.cos(text_angle), -math.sin(text_angle), math.sin(text_angle),
                                      math.cos(text_angle), word.polygon[3].x * scale,
                                      page_height - word.polygon[3].y * scale)
                text.setHorizScale(desired_text_width / actual_text_width * 100)
                text.textOut(word.content + " ")

            pdf_canvas.drawText(text)
            pdf_canvas.save()

            # Move to the beginning of the buffer
            ocr_overlay.seek(0)

            # Add original page and overlay text to the output PDF
            new_pdf_page = PdfReader(ocr_overlay)
            output.add_page(original_page)
            output.add_page(new_pdf_page.pages[0])

    # Save output searchable PDF file
    with open(output_file, "wb") as outputStream:
        output.write(outputStream)

    print(f"Searchable PDF is created: {output_file}")

# Run the script
if __name__ == '__main__':
    main()