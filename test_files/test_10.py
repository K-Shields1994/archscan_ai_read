import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

# Replace these with your Azure Form Recognizer endpoint and key
endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
key = "18ce006f0ac44579a36bfaf01653254c"

# Initialize DocumentAnalysisClient
document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

# Function to analyze the PDF with Azure Document Intelligence READ
def analyze_pdf(file_path):
    # Read the PDF file
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    # Start analysis with the prebuilt "read" model
    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-read", pdf_bytes
    )

    # Wait for the operation to complete and get the result
    result = poller.result()

    # Return the analysis result
    return result

# Function to scale coordinates to match the PDF dimensions
def scale_coordinates(bounding_box, pdf_width, pdf_height, azure_width, azure_height):
    scaled_box = []
    for point in bounding_box:
        x, y = point
        # Convert to float to handle Decimal and float type issues
        scaled_x = (float(x) / float(azure_width)) * float(pdf_width)
        scaled_y = (float(y) / float(azure_height)) * float(pdf_height)
        scaled_box.append((scaled_x, scaled_y))
    return scaled_box

# Function to create a searchable overlay PDF from Azure READ results
def create_overlay_from_result(result, output_pdf, original_pdf_size):
    packet = BytesIO()
    pdf_width, pdf_height = original_pdf_size

    # Use reportlab canvas to create a new PDF
    can = canvas.Canvas(packet, pagesize=(pdf_width, pdf_height))
    
    for page in result.pages:
        azure_width, azure_height = page.width, page.height  # Dimensions from the Azure output
        for line in page.lines:
            # Extract text and its bounding box
            text = line.content
            bounding_box = [(p.x, p.y) for p in line.polygon]
            
            # Scale the bounding box to match the PDF's dimensions
            scaled_box = scale_coordinates(bounding_box, pdf_width, pdf_height, azure_width, azure_height)

            # Use the first point of the bounding box as the position for the text
            if scaled_box:
                x, y = scaled_box[0]
                can.setFillAlpha(0)  # Make text invisible
                can.drawString(x, y, text)
        
        can.showPage()  # Create a new page for each PDF page

    can.save()

    # Move to the beginning of the BytesIO buffer
    packet.seek(0)

    # Create a new PDF with the overlay text
    new_pdf = PdfReader(packet)
    original_pdf = PdfReader(output_pdf)
    
    # Add the overlay to the original PDF
    output = PdfWriter()

    for page_number in range(len(original_pdf.pages)):
        page = original_pdf.pages[page_number]
        overlay_page = new_pdf.pages[page_number]

        # Merge the overlay text onto the original page
        page.merge_page(overlay_page)
        output.add_page(page)

    # Sanitize the output file name
    output_pdf_name = os.path.basename(output_pdf)  # Get the file name
    output_pdf_name = output_pdf_name.replace(":", "").replace("/", "_")  # Remove invalid characters
    
    # Create the new output file path
    output_file_path = os.path.join(os.path.dirname(output_pdf), f"searchable_{output_pdf_name}")

    # Write the output to a new PDF file
    with open(output_file_path, "wb") as output_pdf_file:
        output.write(output_pdf_file)

    print(f"Searchable PDF saved as {output_file_path}")

# Main function that ties everything together
def overlay_text_on_pdf(pdf_file):
    print(f"Analyzing {pdf_file}...")
    result = analyze_pdf(pdf_file)
    
    # Extract the PDF size from the original document (assuming all pages have the same size)
    original_pdf = PdfReader(pdf_file)
    first_page = original_pdf.pages[0]
    original_pdf_size = (float(first_page.mediabox.width), float(first_page.mediabox.height))

    # Create the overlay and merge it with the original PDF
    create_overlay_from_result(result, pdf_file, original_pdf_size)

if __name__ == "__main__":
    # Provide the paths to the PDF files
    pdf_files = [
        r"C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P001.pdf", 
        r"C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P002.pdf"
    ]

    for pdf_file in pdf_files:
        overlay_text_on_pdf(pdf_file)
