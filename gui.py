import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk


def run_gui(handle_process_function):

    #Initialize variables for input and output folders
    input_folder = None
    output_folder = None

    #Helper functions
    def upload_folder():
        nonlocal input_folder
        input_folder = filedialog.askdirectory()
        folder_label.config(text=f"Input: {input_folder}")

    def choose_output_folder():
        nonlocal output_folder
        output_folder = filedialog.askdirectory()
        destination_label.config(text=f"Output: {output_folder}")

    def run_process():
        if input_folder and output_folder:
            handle_process_function(input_folder, output_folder)
            status_label.config(text="Processing complete!")
        else:
            status_label.config(text="Please select both input and output folders.")

    #Set up GUI window 
    root = tk.Tk()
    root.title("Document OCR Tool")
    root.geometry('900x700')
    root.grid_columnconfigure(0, weight=1)

    #Header Frame with Title
    header_frame = tk.Frame(root, bg='#4a90e2', height=60)
    header_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')
    title_label = tk.Label(header_frame, text='File Reader', font=('Helvetica', 24, 'bold'), fg='white',
                           bg='#4a90e2')
    title_label.grid(row=0, column=0, padx=10, pady=20)

    #Center title label in header frame 
    header_frame.grid_rowconfigure(0, weight=1)
    header_frame.grid_columnconfigure(0, weight=1)

    #Main frame for content 
    main_frame = tk.Frame(root, bg='#f0f0f0')
    main_frame.grid(row=1, column=0, padx=20, pady=20, sticky='nsew')
    main_frame.grid_columnconfigure(0, weight=1)

    # Create button frame
    button_frame = tk.Frame(main_frame)
    button_frame.grid(row=0, column=0, padx=10, pady=10)

    # Button to upload folder
    upload_button = tk.Button(button_frame, text="Select Input Folder", command=upload_folder,
                              font=("Helvetica", 12), bg="#4a90e2", fg="white", padx=10, pady=5)
    upload_button.grid(row=0, column=0, padx=10)

    # Button to choose output folder
    output_button = tk.Button(button_frame, text="Select Output Folder", command=choose_output_folder,
                              font=("Helvetica", 12), bg="#4a90e2", fg="white", padx=10, pady=5)
    output_button.grid(row=0, column=1, padx=10)

    # Label to display selected input folder
    folder_label = tk.Label(button_frame, text="No input folder selected", font=("Helvetica", 12), bg="#f0f0f0")
    folder_label.grid(row=1, column=0, pady=5)

    # Label to display selected output folder
    destination_label = tk.Label(button_frame, text="No output folder selected", font=("Helvetica", 12), bg="#f0f0f0")
    destination_label.grid(row=1, column=1, pady=5)

    # Button to run the process
    run_button = tk.Button(button_frame, text="Run", command=run_process,font=("Helvetica", 12),
                           bg="#4a90e2", fg="white", padx=10, pady=5)
    run_button.grid(row=0, column=3, pady=10)

    # Output area to display the results
    output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=100, height=25, font=("Courier", 10))
    output_text.grid(row=4, column=0, pady=10)

    # Output status label
    status_label = tk.Label(root, text="")
    status_label.grid(row=5, column=0, pady=5)

    # Footer with progress bar
    footer_frame = tk.Frame(main_frame, bg='#f0f0f0', height=40)
    footer_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
    footer_frame.grid_columnconfigure(0, weight=1)

    progress_bar = ttk.Progressbar(footer_frame, orient="horizontal", mode="indeterminate", length=400)
    progress_bar.grid(row=0, column=0, pady=10)

    root.mainloop()