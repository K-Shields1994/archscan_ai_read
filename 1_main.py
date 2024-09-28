import sys
import io
import math
import json
import os
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from PIL import Image, ImageSequence
from pypdf import PdfWriter, PdfReader
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


# Function to load Azure credentials from a text file
def load_azure_credentials(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            endpoint = lines[0].split('=')[1].strip().strip('"')
            api_key = lines[1].split('=')[1].strip().strip('"')
        return endpoint, api_key
    except Exception as e:
        raise Exception(f"Error reading Azure credentials from file: {e}")


def dist(p1, p2):
    return math.sqrt((p1.x - p2.x) * (p1.x - p2.x) + (p1.y - p2.y) * (p1.y - p2.y))


def process_pdf(input_folder, output_folder, filename, endpoint, api_key):
    try:
        input_file = os.path.join(input_folder, filename)
        output_pdf_file = os.path.join(output_folder, filename.replace('.pdf', '.ocr.pdf'))
        json_output_file = os.path.join(output_folder, filename.replace('.pdf', '.json'))

        # Loading input file
        print(f"Loading input file {input_file}")
        if input_file.lower().endswith('.pdf'):
            # read existing PDF as images
            image_pages = convert_from_path(input_file)
        else:
            print(f"Error: Unsupported input file extension for {input_file}")
            return

        # Running OCR using Azure Form Recognizer Read API
        print(f"Starting Azure Form Recognizer OCR process for {filename}...")
        document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

        with open(input_file, "rb") as f:
            poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=f)

        ocr_results = poller.result()
        print(f"Azure Form Recognizer finished OCR text for {len(ocr_results.pages)} pages in {filename}.")

        # Save OCR results to JSON file
        with open(json_output_file, "w") as json_file:
            json.dump(ocr_results.to_dict(), json_file, indent=4)

        # Generate OCR overlay layer
        print(f"Generating searchable PDF for {filename}...")
        output = PdfWriter()
        default_font = "Times-Roman"
        for page_id, page in enumerate(ocr_results.pages):
            ocr_overlay = io.BytesIO()

            # Calculate overlay PDF page size
            if image_pages[page_id].height > image_pages[page_id].width:
                page_scale = float(image_pages[page_id].height) / pagesizes.letter[1]
            else:
                page_scale = float(image_pages[page_id].width) / pagesizes.letter[1]

            page_width = float(image_pages[page_id].width) / page_scale
            page_height = float(image_pages[page_id].height) / page_scale

            scale = (page_width / page.width + page_height / page.height) / 2.0
            pdf_canvas = canvas.Canvas(ocr_overlay, pagesize=(page_width, page_height))

            # Add image into PDF page
            pdf_canvas.drawInlineImage(image_pages[page_id], 0, 0, width=page_width, height=page_height,
                                       preserveAspectRatio=True)

            text = pdf_canvas.beginText()
            # Set text rendering mode to invisible
            text.setTextRenderMode(3)
            for word in page.words:
                # Calculate optimal font size
                desired_text_width = max(dist(word.polygon[0], word.polygon[1]),
                                         dist(word.polygon[3], word.polygon[2])) * scale
                desired_text_height = max(dist(word.polygon[1], word.polygon[2]),
                                          dist(word.polygon[0], word.polygon[3])) * scale
                font_size = desired_text_height
                actual_text_width = pdf_canvas.stringWidth(word.content, default_font, font_size)

                # Calculate text rotation angle
                text_angle = math.atan2(
                    (word.polygon[1].y - word.polygon[0].y + word.polygon[2].y - word.polygon[3].y) / 2.0,
                    (word.polygon[1].x - word.polygon[0].x + word.polygon[2].x - word.polygon[3].x) / 2.0)
                text.setFont(default_font, font_size)
                text.setTextTransform(math.cos(text_angle), -math.sin(text_angle), math.sin(text_angle),
                                      math.cos(text_angle),
                                      word.polygon[3].x * scale, page_height - word.polygon[3].y * scale)
                text.setHorizScale(desired_text_width / actual_text_width * 100)
                text.textOut(word.content + " ")

            pdf_canvas.drawText(text)
            pdf_canvas.save()

            # Move to the beginning of the buffer
            ocr_overlay.seek(0)

            # Create a new PDF page
            new_pdf_page = PdfReader(ocr_overlay)
            output.add_page(new_pdf_page.pages[0])

        # Save output searchable PDF file
        with open(output_pdf_file, "wb") as outputStream:
            output.write(outputStream)

        print(f"Searchable PDF created: {output_pdf_file}")
        print(f"OCR results saved as JSON: {json_output_file}")

    except Exception as e:
        print(f"Failed to process {filename}: {e}")


def handle_folder_upload(input_folder, output_folder, endpoint, api_key):
    """Process PDFs from the input folder and save output in the output folder."""
    result = ""
    try:
        os.makedirs(output_folder, exist_ok=True)

        with ThreadPoolExecutor() as executor:
            pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
            for pdf in pdf_files:
                result += f"Processing {pdf}\n"
                executor.submit(process_pdf, input_folder, output_folder, pdf, endpoint, api_key)

        result += "Processing completed successfully!\n"
    except Exception as e:
        result = f"Error during processing: {e}"

    return result


def start_gui():
    """Starts the Tkinter GUI and allows users to choose folders."""
    # Initialize variables to hold selected folders and credentials
    selected_input_folder = None
    selected_output_folder = None
    credentials_file_path = "azure_credentials.txt"  # Path to the credentials file

    try:
        endpoint, api_key = load_azure_credentials(credentials_file_path)
        print(f"Azure endpoint and key loaded successfully!")
    except Exception as e:
        print(f"Failed to load credentials: {e}")
        messagebox.showerror("Error", f"Failed to load credentials: {e}")
        return

    def upload_folder():
        nonlocal selected_input_folder
        selected_input_folder = filedialog.askdirectory(title="Choose Input Folder")
        folder_label.config(
            text=f"Input folder: {selected_input_folder}" if selected_input_folder else "No folder selected")

    def choose_output_folder():
        nonlocal selected_output_folder
        selected_output_folder = filedialog.askdirectory(title="Choose Output Folder")
        destination_label.config(
            text=f"Output folder: {selected_output_folder}" if selected_output_folder else "No folder selected")

    def run_process():
        if not selected_input_folder or not selected_output_folder:
            messagebox.showwarning("Error", "Please select both input and output folders!")
            return

        status_label.config(text="Processing...")
        result = handle_folder_upload(selected_input_folder, selected_output_folder, endpoint, api_key)
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, result)
        status_label.config(text="Processing completed!")

    # Initialize Tkinter GUI
    root = tk.Tk()
    root.title("PDF OCR Processor")
    root.geometry("600x500")

    # Labels and buttons for folder selection
    upload_button = tk.Button(root, text="Select Input Folder", command=upload_folder)
    upload_button.pack(pady=10)

    folder_label = tk.Label(root, text="No input folder selected")
    folder_label.pack(pady=10)

    output_button = tk.Button(root, text="Select Output Folder", command=choose_output_folder)
    output_button.pack(pady=10)

    destination_label = tk.Label(root, text="No output folder selected")
    destination_label.pack(pady=10)

    # Button to run the process
    run_button = tk.Button(root, text="Run", command=run_process)
    run_button.pack(pady=20)

    # Text area for displaying results
    output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10)
    output_text.pack(pady=10)

    # Status label
    status_label = tk.Label(root, text="")
    status_label.pack(pady=10)

    # Start the Tkinter main loop
    root.mainloop()


if __name__ == '__main__':
    start_gui()
