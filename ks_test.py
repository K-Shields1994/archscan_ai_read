import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# Set up Azure Form Recognizer details
endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
api_key = "18ce006f0ac44579a36bfaf01653254c"
document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

# Path to the document (PDF or image) that you want to analyze
document_path = "/Users/kevinshieldsjr/Desktop/lf_test/sample/GU-LF-003737_P002.pdf"

# Step 1: Upload the document and start the analysis using the prebuilt OCR model
with open(document_path, "rb") as document_file:
    poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=document_file)

# Step 2: Wait for the result
result = poller.result()

# Step 3: Print out the results (for each page)
for page in result.pages:
    print(f"Page number: {page.page_number}")
    for line in page.lines:
        print(f"Line: {line.content}")

print("OCR process completed.")