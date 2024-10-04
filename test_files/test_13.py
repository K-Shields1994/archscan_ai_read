import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import fitz  # PyMuPDF

# Set up your Azure credentials and endpoint
endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
api_key = "18ce006f0ac44579a36bfaf01653254c"

# Create a client to interact with the Azure API
document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(api_key)
)

# Function to perform OCR using Azure's Prebuilt Read API
def extract_text_from_pdf(pdf_path):
    extracted_text = {}
    
    # Read the PDF and perform OCR
    with open(pdf_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document(
            "prebuilt-read", document=f
        )
    result = poller.result()

    # Extract the text from the OCR process and organize it by page
    for page_idx, page in enumerate(result.pages):
        page_text = ""
        for line in page.lines:
            page_text += line.content + "\n"
        extracted_text[page_idx] = page_text  # Store text by page number

    return extracted_text

# Function to overlay extracted text onto the original PDF
def overlay_text_on_pdf(input_pdf, output_pdf, extracted_text):
    # Open the original PDF
    doc = fitz.open(input_pdf)
    
    # Iterate through the pages and overlay the extracted text
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = extracted_text.get(page_num, "")
        
        # Add the text as a searchable text layer
        text_rect = page.rect  # Use the entire page
        page.insert_text(text_rect.tl, text, fontsize=10, color=(0, 0, 0))  # Insert black text at the top-left

    # Save the modified PDF
    doc.save(output_pdf)
    print(f"Searchable PDF saved to: {output_pdf}")
    doc.close()

# Main function to handle the full process
def process_pdf(input_pdf, output_pdf):
    # Step 1: Extract text from the PDF using Azure's Prebuilt Read API
    print("Extracting text using Azure OCR...")
    extracted_text = extract_text_from_pdf(input_pdf)

    # Step 2: Overlay the extracted text onto the original PDF
    print("Overlaying text onto the PDF...")
    overlay_text_on_pdf(input_pdf, output_pdf, extracted_text)

    print(f"Process complete! Searchable PDF saved to: {output_pdf}")

# Example usage:
input_pdf_path = "C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P001.pdf"  # Replace with the path to your input PDF
output_pdf_path = "C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/searchable_PGCPS-LF-03384_P001.pdf"  # Replace with the desired output path

# Run the combined process
process_pdf(input_pdf_path, output_pdf_path)
