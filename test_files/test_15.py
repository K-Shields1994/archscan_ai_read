import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult

# List of common English words (stop words) to exclude from the output text files
STOP_WORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at", "be",
    "because", "been", "before", "being", "below", "between", "both", "but", "by", "could", "did", "do", "does",
    "doing", "down", "during", "each", "few", "for", "from", "further", "had", "has", "have", "having", "he",
    "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should",
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your",
    "yours", "yourself", "yourselves"
])

def start_gui(handle_folder_upload):
    """
    Starts the Tkinter GUI and handles user interactions.
    """
    def upload_folder():
        input_folder_path = filedialog.askdirectory(title="Choose a folder containing PDF files")
        if input_folder_path:
            input_folder_label.config(text=f"Input folder: {os.path.basename(input_folder_path)}")
            output_folder_path = filedialog.askdirectory(title="Choose a folder to save the results")
            if output_folder_path:
                output_folder_label.config(text=f"Output folder: {os.path.basename(output_folder_path)}")
                status_label.config(text="Processing...")
                progress_bar.start()
                result = handle_folder_upload(input_folder_path, output_folder_path)
                progress_bar.stop()
                output_text.delete(1.0, tk.END)
                output_text.insert(tk.END, result)
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
    root.configure(bg='#f0f0f0')

    # Header with Title
    header_frame = tk.Frame(root, bg='#4a90e2', height=60)
    header_frame.pack(fill='x')
    title_label = tk.Label(header_frame, text="PDF Analyzer", font=("Helvetica", 24, "bold"), fg='white', bg='#4a90e2')
    title_label.pack(pady=10)

    # Main Frame for Content
    main_frame = tk.Frame(root, bg='#f0f0f0')
    main_frame.pack(padx=20, pady=20, fill='both', expand=True)

    # Upload Button
    upload_button = tk.Button(main_frame, text="Upload Folder", command=upload_folder, font=("Helvetica", 12),
                              bg="#4a90e2", fg="white", padx=10, pady=5)
    upload_button.pack(pady=10)

    # Labels for Selected Folders
    input_folder_label = tk.Label(main_frame, text="No input folder selected", font=("Helvetica", 12), bg="#f0f0f0")
    input_folder_label.pack(pady=5)
    output_folder_label = tk.Label(main_frame, text="No output folder selected", font=("Helvetica", 12), bg="#f0f0f0")
    output_folder_label.pack(pady=5)

    # Output Area for Results
    output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=100, height=25, font=("Courier", 10))
    output_text.pack(pady=10)

    # Status Label
    status_label = tk.Label(main_frame, text="", font=("Helvetica", 10), bg="#f0f0f0", fg="#4a90e2")
    status_label.pack(pady=5)

    # Footer with Progress Bar
    footer_frame = tk.Frame(root, bg='#f0f0f0')
    footer_frame.pack(fill='x', pady=10)
    progress_bar = ttk.Progressbar(footer_frame, orient="horizontal", mode="indeterminate", length=400)
    progress_bar.pack(pady=10)

    root.mainloop()

def handle_folder_upload(input_folder_path, output_folder_path):
    """
    Processes all PDF files in the selected input folder and saves the results to the output folder.
    """
    endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
    key = "18ce006f0ac44579a36bfaf01653254c"
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    result_summary = ""

    # Iterate over all PDF files in the input folder
    for filename in os.listdir(input_folder_path):
        if filename.lower().endswith(".pdf"):
            input_file_path = os.path.join(input_folder_path, filename)
            input_file_name = os.path.splitext(filename)[0]

            try:
                # Analyze the PDF
                with open(input_file_path, "rb") as f:
                    poller = document_intelligence_client.begin_analyze_document(
                        "prebuilt-read",
                        analyze_request=f,
                        output=[AnalyzeOutputOption.PDF],
                        content_type="application/octet-stream",
                    )
                    result: AnalyzeResult = poller.result()

                # Output file paths
                pdf_output_file = os.path.join(output_folder_path, f"{input_file_name}.pdf")
                json_output_file = os.path.join(output_folder_path, f"{input_file_name}.json")
                txt_output_file = os.path.join(output_folder_path, f"{input_file_name}_filtered.txt")

                # Save the analyzed PDF
                response = document_intelligence_client.get_analyze_result_pdf(
                    model_id=result.model_id, result_id=poller.details["operation_id"]
                )
                with open(pdf_output_file, "wb") as writer:
                    writer.writelines(response)

                # Save the JSON output
                result_json = result.as_dict()
                with open(json_output_file, "w") as json_file:
                    json.dump(result_json, json_file, indent=4)

                # Extract and filter words, then save to a text file
                with open(txt_output_file, "w") as text_file:
                    for page in result_json.get("pages", []):
                        for line in page.get("lines", []):
                            content = line.get("content", "")
                            words = content.split()
                            filtered_words = [word for word in words if word.lower() not in STOP_WORDS]
                            text_file.write("\n".join(filtered_words) + "\n")

                result_summary += f"Processed: {filename}\n"
            except Exception as e:
                result_summary += f"Failed to process {filename}: {str(e)}\n"

    return result_summary

# Start the GUI
start_gui(handle_folder_upload)