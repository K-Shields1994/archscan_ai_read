from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
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

# Function to create a searchable overlay PDF from Azure READ results
def create_overlay_from_result(result, output_pdf):
    packet = BytesIO()
    # Use reportlab canvas to create a new PDF
    can = canvas.Canvas(packet, pagesize=letter)
    
    for page in result.pages:
        for line in page.lines:
            # Extract text and its bounding box
            text = line.content
            bounding_box = [(p.x, p.y) for p in line.polygon]
            
            # Draw the text at the given bounding box (adjust based on PDF coordinates)
            # Here we are using (x, y) from the bounding box (adjust this as needed)
            if bounding_box:
                x, y = bounding_box[0]
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

    # Write the output to a new PDF file
    with open(f"searchable_{output_pdf}", "wb") as output_pdf_file:
        output.write(output_pdf_file)

    print(f"Searchable PDF saved as searchable_{output_pdf}")

# Main function that ties everything together
def overlay_text_on_pdf(pdf_file):
    print(f"Analyzing {pdf_file}...")
    result = analyze_pdf(pdf_file)
    
    # Create the overlay and merge it with the original PDF
    create_overlay_from_result(result, pdf_file)

if __name__ == "__main__":
    # Provide the paths to the PDF files
    pdf_files = ["C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P001.pdf", "C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P002.pdf"]

    for pdf_file in pdf_files:
        overlay_text_on_pdf(pdf_file)
