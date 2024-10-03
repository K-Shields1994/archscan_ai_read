import sys  # System-specific parameters and functions
import io  # Core tools for working with input and output
import math  # Provides access to mathematical functions
from pypdf import PdfWriter, PdfReader  # Handles PDF creation and reading
from reportlab.pdfgen import canvas  # Generates PDFs in memory
from reportlab.lib import pagesizes  # Provides various page size constants
from azure.core.credentials import AzureKeyCredential  # Authentication for Azure services
from azure.ai.formrecognizer import DocumentAnalysisClient  # Handles document analysis with Azure Form Recognizer

# Azure Form Recognizer endpoint and key for authentication
endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
key = "18ce006f0ac44579a36bfaf01653254c"

# File paths for the input PDF and output searchable PDF
input_file = '/Volumes/SSD/pg_hs/1_test/PGCPS-LF-03384/PGCPS-LF-03384_P001.pdf'
output_file = '/Volumes/SSD/pg_hs/1_test/PGCPS-LF-03384/PGCPS-LF-03384_P001_ocr.pdf'

# Main function to run OCR and create a searchable PDF
def main():
    # Load the input file and verify it's a PDF
    print(f"1. Loading input file {input_file}")
    if not input_file.lower().endswith('.pdf'):
        sys.exit(f"Error: Unsupported input file extension {input_file}. Supported extension: PDF")

    # Initialize Azure Form Recognizer client and start OCR process
    print(f"2. Starting Azure Form Recognizer OCR process...")
    document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # Open the input PDF file in binary mode for processing. "rb" means "read binary"
    with open(input_file, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=f)

    # Retrieve OCR results from Azure after processing
    ocr_results = poller.result()
    print(f"3. Azure Form Recognizer finished OCR text for {len(ocr_results.pages)} pages.")

    # Create a PDF writer to generate the final searchable PDF
    print(f"5. Generating searchable PDF...")
    output = PdfWriter()
    default_font = "Times-Roman"  # Set default font for the OCR text layer

    # Open the original PDF to use as a background
    with open(input_file, "rb") as input_pdf_stream:
        original_pdf = PdfReader(input_pdf_stream)

        # Loop through each page to apply the OCR overlay
        for page_id, page in enumerate(ocr_results.pages):
            ocr_overlay = io.BytesIO()  # Buffer for the OCR overlay

            # Get original page dimensions from the PDF
            original_page = original_pdf.pages[page_id]
            page_width = original_page.mediabox.width
            page_height = original_page.mediabox.height

            # Calculate the scaling factor for the OCR text overlay
            scale = (page_width / page.width + page_height / page.height) / 2.0
            pdf_canvas = canvas.Canvas(ocr_overlay, pagesize=(page_width, page_height))

            # Start text mode to overlay the OCR results
            text = pdf_canvas.beginText()
            text.setTextRenderMode(3)  # Set text mode to invisible so it doesn't overlap visually

            # Loop through words on the page and place them on the PDF canvas
            for word in page.words:
                word_width = word.polygon[1].x - word.polygon[0].x
                word_height = word.polygon[3].y - word.polygon[0].y
                font_size = word_height * scale
                actual_text_width = pdf_canvas.stringWidth(word.content, default_font, font_size)

                if actual_text_width == 0:
                    actual_text_width = 1  # Avoid zero division error

                # Adjust the position to match the original document
                x_position = word.polygon[0].x * scale
                y_position = page_height - word.polygon[0].y * scale  # Flip the y-axis for PDF coordinates

                # Calculate text rotation angle based on word orientation
                dx = word.polygon[1].x - word.polygon[0].x
                dy = word.polygon[1].y - word.polygon[0].y
                text_angle = math.atan2(dy, dx)  # Calculate angle of text from the first two points

                # Set the font and place the word in the correct position and orientation
                text.setFont(default_font, font_size)
                text.setTextTransform(
                    math.cos(text_angle), -math.sin(text_angle),
                    math.sin(text_angle), math.cos(text_angle),
                    x_position, y_position
                )

                # Adjust text width scaling
                text.setHorizScale((word_width * scale) / actual_text_width * 100)
                text.textOut(word.content + " ")  # Add the OCR text to the canvas

            pdf_canvas.drawText(text)  # Finalize text overlay
            pdf_canvas.save()  # Save the overlay to the buffer

            # Move to the beginning of the buffer for reading
            ocr_overlay.seek(0)

            # Merge the OCR overlay with the original PDF page
            overlay_pdf = PdfReader(ocr_overlay)
            original_page.merge_page(overlay_pdf.pages[0])  # Merge the original page with the OCR overlay

            # Add the merged page (original + OCR overlay) to the final output PDF
            output.add_page(original_page)

    # Write the final searchable PDF to the specified output file
    with open(output_file, "wb") as outputStream:
        output.write(outputStream)

    print(f"6. Searchable PDF is created: {output_file}")


# Execute the main function when the script is run directly
if __name__ == '__main__':
    main()