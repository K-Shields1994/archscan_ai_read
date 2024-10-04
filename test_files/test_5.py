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
    # The polygon will have four points, and we can use the top-left (0) and top-right (1) to calculate the angle
    dx = polygon[1].x - polygon[0].x
    dy = polygon[1].y - polygon[0].y
    angle = math.degrees(math.atan2(dy, dx))
    return angle


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

            # Get original page dimensions and rotation
            original_page = original_pdf.pages[page_id]
            page_width = original_page.mediabox.width
            page_height = original_page.mediabox.height

            # Get the rotation metadata for the page
            rotation = original_page.get('/Rotate', 0)
            print(f"Page {page_id}: Rotation = {rotation}, Page Width = {page_width}, Page Height = {page_height}")

            # Adjust scaling factors individually for X and Y axes
            x_scale = page_width / page.width
            y_scale = page_height / page.height

            # Create the canvas for the OCR text overlay
            pdf_canvas = canvas.Canvas(ocr_overlay, pagesize=(page_width, page_height))

            # Apply rotation if needed
            if rotation != 0:
                pdf_canvas.translate(page_width / 2, page_height / 2)
                pdf_canvas.rotate(rotation)
                pdf_canvas.translate(-page_width / 2, -page_height / 2)

            # Set up the text object for invisible OCR text
            text = pdf_canvas.beginText()
            text.setTextRenderMode(3)  # Invisible text

            # Loop through each word in the OCR results and place them on the page
            for word in page.words:
                word_width = word.polygon[1].x - word.polygon[0].x
                word_height = word.polygon[3].y - word.polygon[0].y
                font_size = word_height * y_scale  # Adjust font size based on Y scaling

                # Calculate text position, flipping Y-axis if necessary
                x_position = word.polygon[0].x * x_scale
                y_position = page_height - word.polygon[0].y * y_scale

                # Calculate the rotation of the word using the polygon coordinates
                word_rotation = calculate_word_rotation(word.polygon)
                print(f"Word: {word.content}, Rotation: {word_rotation:.2f} degrees, X: {x_position:.2f}, Y: {y_position:.2f}")

                # Apply the rotation for each word around its own coordinates
                text.setFont(default_font, font_size)

                # Apply rotation and translation individually for each word
                text.setTextTransform(
                    math.cos(math.radians(word_rotation)),
                    math.sin(math.radians(word_rotation)),
                    -math.sin(math.radians(word_rotation)),
                    math.cos(math.radians(word_rotation)),
                    x_position,
                    y_position
                )

                # Render the word as invisible text
                text.textOut(word.content + " ")

            # Draw the invisible text on the canvas
            pdf_canvas.drawText(text)
            pdf_canvas.save()

            ocr_overlay.seek(0)

            # Merge the OCR overlay with the original PDF page
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
