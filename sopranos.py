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


# Function to calculate the Euclidean distance between two points (p1, p2) in a 2D space
def dist(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


# Main function to run OCR and create a searchable PDF
def main():
    # Load the input file and verify it's a PDF
    print(f"Loading input file {input_file}")
    if not input_file.lower().endswith('.pdf'):
        sys.exit(f"Error: Unsupported input file extension {input_file}. Supported extension: PDF")

    # Initialize Azure Form Recognizer client and start OCR process
    print(f"Starting Azure Form Recognizer OCR process...")
    document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # Open the input PDF file in binary mode for processing
    with open(input_file, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=f)

    # Retrieve OCR results from Azure after processing
    ocr_results = poller.result()
    print(f"Azure Form Recognizer finished OCR text for {len(ocr_results.pages)} pages.")

    # Create a PDF writer to generate the final searchable PDF
    print(f"Generating searchable PDF...")
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
                # Calculate optimal font size based on the word's bounding box
                desired_text_width = max(dist(word.polygon[0], word.polygon[1]),
                                         dist(word.polygon[3], word.polygon[2])) * scale
                desired_text_height = max(dist(word.polygon[1], word.polygon[2]),
                                          dist(word.polygon[0], word.polygon[3])) * scale
                font_size = desired_text_height
                actual_text_width = pdf_canvas.stringWidth(word.content, default_font, font_size)

                # Calculate text rotation angle based on word orientation
                text_angle = math.atan2(
                    (word.polygon[1].y - word.polygon[0].y + word.polygon[2].y - word.polygon[3].y) / 2.0,
                    (word.polygon[1].x - word.polygon[0].x + word.polygon[2].x - word.polygon[3].x) / 2.0)
                text.setFont(default_font, font_size)
                text.setTextTransform(math.cos(text_angle), -math.sin(text_angle), math.sin(text_angle),
                                      math.cos(text_angle), word.polygon[3].x * scale,
                                      page_height - word.polygon[3].y * scale)
                text.setHorizScale(desired_text_width / actual_text_width * 100)  # Adjust text width scaling
                text.textOut(word.content + " ")  # Add the OCR text to the canvas

            pdf_canvas.drawText(text)  # Finalize text overlay
            pdf_canvas.save()  # Save the overlay to the buffer

            # Move to the beginning of the buffer for reading
            ocr_overlay.seek(0)

            # Add original PDF page and the OCR overlay to the output PDF
            new_pdf_page = PdfReader(ocr_overlay)
            output.add_page(original_page)  # Add original background page
            output.add_page(new_pdf_page.pages[0])  # Add the OCR overlay

    # Write the final searchable PDF to the specified output file
    with open(output_file, "wb") as outputStream:
        output.write(outputStream)

    print(f"Searchable PDF is created: {output_file}")


# Execute the main function when the script is run directly
if __name__ == '__main__':
    main()
