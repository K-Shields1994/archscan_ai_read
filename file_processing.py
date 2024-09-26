import os
import requests


def process_folder(endpoint, api_key, input_folder, json_output_path, unsupported_log_path, output_folder_path):
    results = []
    unsupported_files = []

    # Ensure the output folder exists for saving OCR-ed PDFs
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)
        if file_name.endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            # Open the file for processing
            with open(file_path, "rb") as f:
                # Use the endpoint and api_key passed from 1_main.py
                headers = {
                    'Ocp-Apim-Subscription-Key': api_key,
                    'Content-Type': 'application/pdf'
                }

                # Send the request to the REST API
                response = requests.post(f"{endpoint}/formrecognizer/v2.1/layout/analyze", headers=headers, data=f)

                # Handle response
                if response.status_code == 202:
                    # Poll for the result (getting the operation-location)
                    operation_location = response.headers['Operation-Location']
                    poll_for_searchable_pdf(operation_location, api_key, output_folder_path, file_name)
                else:
                    print(f"Failed to process {file_name}, Status Code: {response.status_code}")

        else:
            unsupported_files.append(file_name)

    return results, unsupported_files


# Polling the API for the PDF results and downloading the file
def poll_for_searchable_pdf(operation_url, api_key, output_folder_path, file_name):
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    # Poll for the result
    while True:
        poll_response = requests.get(operation_url, headers=headers)
        result = poll_response.json()

        if poll_response.status_code == 200 and result['status'] == 'succeeded':
            # Get the searchable PDF URL from the result
            pdf_url = result['analyzeResult']['contentUrl']
            download_pdf(pdf_url, output_folder_path, file_name)
            break
        elif poll_response.status_code == 200 and result['status'] == 'failed':
            print(f"Document analysis failed for {file_name}.")
            break

    print("Searchable PDF process complete.")


# Download the PDF from Azure API
def download_pdf(pdf_url, output_folder_path, file_name):
    response = requests.get(pdf_url)
    pdf_output_path = os.path.join(output_folder_path, file_name)

    with open(pdf_output_path, 'wb') as output_pdf:
        output_pdf.write(response.content)

    print(f"Searchable PDF saved to {pdf_output_path}")
