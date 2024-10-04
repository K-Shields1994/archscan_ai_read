import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import ocrmypdf

# Set up your Azure credentials and endpoint
endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
api_key = "18ce006f0ac44579a36bfaf01653254c"

# Create a client to interact with the API
document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(api_key)
)

# Function to perform OCR using Azure's Prebuilt Read API
def extract_text_from_pdf(pdf_path):
    extracted_text = ""
    
    # Read the PDF and perform OCR
    with open(pdf_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document(
            "prebuilt-read", document=f
        )
    result = poller.result()

    # Extract the text from the OCR process
    for page in result.pages:
        for line in page.lines:
            extracted_text += line.content + "\n"

    return extracted_text

# Function to apply OCRmyPDF to the PDF
def make_pdf_searchable(input_pdf, output_pdf):
    # Apply OCR to make the PDF searchable
    ocrmypdf.ocr(input_pdf, output_pdf, force_ocr=True, output_type="pdf")

# Main function to handle the full process
def process_pdf(input_pdf, output_pdf):
    # Step 1: Extract text from the PDF using Azure's Prebuilt Read API
    print("Extracting text using Azure OCR...")
    extracted_text = extract_text_from_pdf(input_pdf)

    # Save the extracted text to a text file (optional)
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(extracted_text)

    # Step 2: Overlay the extracted text onto the original PDF using OCRmyPDF
    print("Making PDF searchable using OCRmyPDF...")
    make_pdf_searchable(input_pdf, output_pdf)

    print(f"Process complete! Searchable PDF saved to: {output_pdf}")

# Example usage:
input_pdf_path = "C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P001.pdf"  # Replace with the path to your input PDF
output_pdf_path = "C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/searchable_PGCPS-LF-03384_P001.pdf"  # Replace with the desired output path

# Run the combined process
process_pdf(input_pdf_path, output_pdf_path)
