from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import json

# Replace these with your Azure Form Recognizer endpoint and key
endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
key = "18ce006f0ac44579a36bfaf01653254c"

# Initialize DocumentAnalysisClient
document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

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

    # Convert the result to JSON
    result_json = {
        "content": result.content,
        "pages": []
    }

    for page in result.pages:
        page_info = {
            "page_number": page.page_number,
            "width": page.width,
            "height": page.height,
            "unit": page.unit,
            "lines": []
        }

        for line in page.lines:
            page_info["lines"].append({
                "text": line.content,
                "bounding_box": [(p.x, p.y) for p in line.polygon]
            })

        result_json["pages"].append(page_info)

    return result_json

if __name__ == "__main__":
    # Paths to the PDFs
    pdf_files = ["C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P001.pdf", "C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P002.pdf"]

    for pdf_file in pdf_files:
        print(f"Analyzing {pdf_file}...")
        result_json = analyze_pdf(pdf_file)
        
        # Save the JSON result to a file
        output_file = pdf_file.replace(".pdf", "_read_result.json")
        with open(output_file, "w") as outfile:
            json.dump(result_json, outfile, indent=4)
        
        print(f"Results saved to {output_file}")
