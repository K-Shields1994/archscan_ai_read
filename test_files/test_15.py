import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult


def start_gui(handle_folder_upload):
    """
    Starts the Tkinter GUI and handles user interactions.
    """

    def upload_folder():
        input_folder_path = filedialog.askdirectory(
            title="Choose a folder containing PDF files"
        )
        if input_folder_path:
            input_folder_label.config(text=f"Input folder: {os.path.basename(input_folder_path)}")

            # Prompt user to select an output folder
            output_folder_path = filedialog.askdirectory(
                title="Choose a folder to save the results"
            )
            if output_folder_path:
                output_folder_label.config(text=f"Output folder: {os.path.basename(output_folder_path)}")

                # Show a progress message
                status_label.config(text="Processing...")

                # Start the progress bar
                progress_bar.start()

                # Call the provided callback function to process the folder
                result = handle_folder_upload(input_folder_path, output_folder_path)

                # Stop the progress bar
                progress_bar.stop()

                # Clear the text area
                output_text.delete(1.0, tk.END)

                # Insert result into the output text area
                output_text.insert(tk.END, result)

                # Update status message
                status_label.config(text="Processing complete.")
            else:
                messagebox.showwarning("No output folder selected", "Please select an output folder to save the results.")
                status_label.config(text="No output folder selected.")
        else:
            messagebox.showwarning("No folder selected", "Please select a folder containing PDF files.")
            status_label.config(text="No input folder selected.")

    # Setup the GUI window
    root = tk.Tk()
    root.title("PDF Analyzer")
    root.geometry("900x700")
    root.configure(bg='#f0f0f0')  # Set background color

    # Header Frame with Title
    header_frame = tk.Frame(root, bg='#4a90e2', height=60)
    header_frame.pack(fill='x')
    title_label = tk.Label(header_frame, text="PDF Analyzer", font=("Helvetica", 24, "bold"), fg='white', bg='#4a90e2')
    title_label.pack(pady=10)

    # Main frame for the content
    main_frame = tk.Frame(root, bg='#f0f0f0')
    main_frame.pack(padx=20, pady=20, fill='both', expand=True)

    # Folder upload button
    upload_button = tk.Button(main_frame, text="Upload Folder", command=upload_folder, font=("Helvetica", 12),
                              bg="#4a90e2", fg="white", padx=10, pady=5)
    upload_button.pack(pady=10)

    # Labels to display selected folders
    input_folder_label = tk.Label(main_frame, text="No input folder selected", font=("Helvetica", 12), bg="#f0f0f0")
    input_folder_label.pack(pady=5)

    output_folder_label = tk.Label(main_frame, text="No output folder selected", font=("Helvetica", 12), bg="#f0f0f0")
    output_folder_label.pack(pady=5)

    # Output area to display the results
    output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=100, height=25, font=("Courier", 10))
    output_text.pack(pady=10)

    # Status label for status updates
    status_label = tk.Label(main_frame, text="", font=("Helvetica", 10), bg="#f0f0f0", fg="#4a90e2")
    status_label.pack(pady=5)

    # Footer with progress bar
    footer_frame = tk.Frame(root, bg='#f0f0f0')
    footer_frame.pack(fill='x', pady=10)

    progress_bar = ttk.Progressbar(footer_frame, orient="horizontal", mode="indeterminate", length=400)
    progress_bar.pack(pady=10)

    root.mainloop()


def handle_folder_upload(input_folder_path, output_folder_path):
    """
    Processes all PDF files in the selected input folder and saves the results to the output folder.
    """
    # Replace with your Azure endpoint and key
    endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
    key = "18ce006f0ac44579a36bfaf01653254c"

    # Create the Document Intelligence client
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    result_summary = ""

    # Loop through all PDF files in the input folder
    for filename in os.listdir(input_folder_path):
        if filename.lower().endswith(".pdf"):
            input_file_path = os.path.join(input_folder_path, filename)
            input_file_name = os.path.splitext(filename)[0]  # Get the base name without the extension

            try:
                # Open the PDF file to be analyzed
                with open(input_file_path, "rb") as f:
                    poller = document_intelligence_client.begin_analyze_document(
                        "prebuilt-read",
                        analyze_request=f,
                        output=[AnalyzeOutputOption.PDF],
                        content_type="application/octet-stream",
                    )
                    result: AnalyzeResult = poller.result()

                # Define output file names based on the input file name
                pdf_output_file = os.path.join(output_folder_path, f"{input_file_name}.pdf")
                json_output_file = os.path.join(output_folder_path, f"{input_file_name}.json")
                txt_output_file = os.path.join(output_folder_path, f"{input_file_name}.txt")

                # Retrieve the PDF and write it to a file
                response = document_intelligence_client.get_analyze_result_pdf(
                    model_id=result.model_id, result_id=poller.details["operation_id"]
                )
                with open(pdf_output_file, "wb") as writer:
                    writer.writelines(response)

                # Convert the analysis result to a JSON-compatible dictionary
                result_json = result.as_dict()

                # Write the JSON output to a file
                with open(json_output_file, "w") as json_file:
                    json.dump(result_json, json_file, indent=4)

                # Extract words from the JSON and save to a text file
                with open(txt_output_file, "w") as text_file:
                    for page in result_json.get("pages", []):
                        for line in page.get("lines", []):
                            content = line.get("content", "")
                            words = content.split()  # Split the content into words
                            for word in words:
                                text_file.write(word + "\n")

                result_summary += f"Processed: {filename}\n"
            except Exception as e:
                result_summary += f"Failed to process {filename}: {str(e)}\n"

    return result_summary


# Start the GUI
start_gui(handle_folder_upload)