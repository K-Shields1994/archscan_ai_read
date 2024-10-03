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


def main():
    # Load the input file
    print(f"Loading input file {input_file}")
    if not input_file.lower().endswith('.pdf'):
        sys.exit(f"Error: Unsupported input file extension {input_file}. Supported extension: PDF")

    # Start OCR process with Azure Form Recognizer
    print(f"Starting Azure Form Recognizer OCR process...")
    document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    with open(input_file, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=f)

    ocr_results = poller.result()
    print(f"OCR completed for {len(ocr_results.pages)} pages.")

    # Create searchable PDF
    output = PdfWriter()
    default_font = "Times-Roman"

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

            # Apply a 180-degree rotation to the entire text overlay
            pdf_canvas.translate(page_width / 2, page_height / 2)  # Move origin to center of the page
            pdf_canvas.rotate(180)  # Rotate the canvas by 180 degrees
            pdf_canvas.translate(-page_width / 2, -page_height / 2)  # Move origin back to the corner

            text = pdf_canvas.beginText()
            text.setTextRenderMode(3)  # Set text rendering mode to invisible

            # Loop through each word in OCR results
            for word in page.words:
                word_width = word.polygon[1].x - word.polygon[0].x
                word_height = word.polygon[3].y - word.polygon[0].y
                font_size = word_height * scale

                # Adjust text position (flipping Y-axis for correct placement)
                x_position = word.polygon[0].x * scale
                y_position = (page_height - word.polygon[0].y * scale)

                # Set font and place the word in the correct position (no rotation per word)
                text.setFont(default_font, font_size)
                text.setTextTransform(1, 0, 0, 1, x_position,
                                      y_position)  # No rotation here, since entire canvas is rotated

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
