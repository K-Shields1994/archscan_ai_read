import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult

endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
key = "18ce006f0ac44579a36bfaf01653254c"

# Define the input folder path containing PDFs
input_folder_path = "/Volumes/SSD/mississippi/USM-LF-0503/"
# Create the Document Intelligence client
document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# Loop through all PDF files in the input folder
for filename in os.listdir(input_folder_path):
    if filename.lower().endswith(".pdf"):
        input_file_path = os.path.join(input_folder_path, filename)
        input_file_name = os.path.basename(input_file_path).split('.')[0]  # Get the base name without the extension

        # Open the PDF file to be analyzed
        with open(input_file_path, "rb") as f:
            poller = document_intelligence_client.begin_analyze_document(
                "prebuilt-read",
                analyze_request=f,
                output=[AnalyzeOutputOption.PDF],
                content_type="application/octet-stream",
            )
            result: AnalyzeResult = poller.result()

        # Get the operation ID for retrieving the PDF result
        operation_id = poller.details["operation_id"]

        # Define output file names based on the input file name
        pdf_output_file = os.path.join(input_folder_path, f"{input_file_name}.pdf")
        json_output_file = os.path.join(input_folder_path, f"{input_file_name}.json")
        txt_output_file = os.path.join(input_folder_path, f"{input_file_name}.txt")

        # Retrieve the PDF and write it to a file
        response = document_intelligence_client.get_analyze_result_pdf(model_id=result.model_id, result_id=operation_id)
        with open(pdf_output_file, "wb") as writer:
            writer.writelines(response)

        # Convert the analysis result to a JSON-compatible dictionary
        result_json = result.as_dict()

        # Write the JSON output to a file
        with open(json_output_file, "w") as json_file:
            json.dump(result_json, json_file, indent=4)

        # Load the JSON result from the previously saved file
        with open(json_output_file, "r") as json_file:
            analyze_data = json.load(json_file)

        # Open a text file to save the extracted words
        with open(txt_output_file, "w") as text_file:
            # Traverse through the JSON structure to find content fields
            for page in analyze_data.get("pages", []):
                for line in page.get("lines", []):
                    content = line.get("content", "")
                    # Write each word from the content to the text file, one word per line
                    words = content.split()  # Split the content into words
                    for word in words:
                        text_file.write(word + "\n")

        print(
            f"Analysis complete for '{filename}'. Results saved to '{pdf_output_file}', '{json_output_file}', and '{txt_output_file}'.")
