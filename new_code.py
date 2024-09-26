import os
import time
import requests
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

# Set up Azure Form Recognizer details
endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
api_key = "18ce006f0ac44579a36bfaf01653254c"
document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

# Set up Azure Blob Storage details
blob_connection_string = "your_blob_storage_connection_string_here"  # Replace with your Blob storage connection string
blob_container_name = "your_container_name_here"  # Replace with your container name

# Path to the document (PDF) that you want to analyze
document_path = "/Users/kevinshieldsjr/Desktop/lf_test/sample/GU-LF-003737_P002.pdf"

# Step 1: Upload the document and start the analysis
with open(document_path, "rb") as document_file:
    poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=document_file)

# Step 2: Wait for the result
result = poller.result()

# Step 3: Prepare the JSON result for saving to Blob Storage
json_result = {
    "pages": [page.to_dict() for page in result.pages],  # Convert the result to a JSON serializable format
}

# Step 4: Set up BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)

# Step 5: Upload JSON result to Blob Storage
json_blob_name = "ocr_analysis_result.json"
json_blob_client = blob_service_client.get_blob_client(container=blob_container_name, blob=json_blob_name)

# Upload JSON file as a string
json_blob_client.upload_blob(str(json_result), overwrite=True)
print(f"JSON result uploaded to blob storage as: {json_blob_name}")

# Step 6: Check if the result contains an OCR-ed searchable PDF (if available)
output_content_url = None
for page_result in result.content:
    if page_result.kind == "content":  # Ensure content type matches
        output_content_url = page_result.url  # URL to the OCR-ed PDF content

# Step 7: If OCR-ed searchable PDF is available, download and upload to Blob Storage
if output_content_url:
    response = requests.get(output_content_url)
    pdf_blob_name = "output_searchable_pdf.pdf"
    pdf_blob_client = blob_service_client.get_blob_client(container=blob_container_name, blob=pdf_blob_name)

    # Upload the PDF file content to Blob Storage
    pdf_blob_client.upload_blob(response.content, overwrite=True)
    print(f"OCR-ed searchable PDF uploaded to blob storage as: {pdf_blob_name}")
else:
    print("No OCR-ed content found.")