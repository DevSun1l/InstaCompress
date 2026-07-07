import tkinter as tk
from tkinter import filedialog, messagebox
import os
from compressor import process_pdf, process_image

def process_files(target_size_kb, file_paths):
    """
    Processes selected PDF and Image files using compressor backend.
    Calculates size reduction and writes output to Desktop/Compressed_Files.
    """
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    output_folder = os.path.join(desktop, "Compressed_Files")
    os.makedirs(output_folder, exist_ok=True)

    print(f"\n--- Starting Compression Pipeline ---")
    print(f"Target File Size: {target_size_kb} KB")
    print(f"Output Directory: {output_folder}")
    print(f"Total Files Selected: {len(file_paths)}")
    print("-------------------------------------")

    for path in file_paths:
        if not os.path.exists(path):
            print(f"File not found: {path}")
            continue

        ext = os.path.splitext(path)[1].lower()
        orig_size = os.path.getsize(path)
        
        try:
            if ext == ".pdf":
                output_path = process_pdf(path, target_size_kb, output_folder)
            elif ext in (".jpg", ".jpeg", ".png"):
                output_path = process_image(path, target_size_kb, output_folder)
            else:
                print(f"Unsupported format: {path}")
                continue
            
            compressed_size = os.path.getsize(output_path)
            reduction = (1 - compressed_size / orig_size) * 100 if orig_size > 0 else 0
            
            print(f"Processed: {os.path.basename(path)}")
            print(f"  - Original Size: {orig_size / 1024:.2f} KB")
            print(f"  - Compressed Size: {compressed_size / 1024:.2f} KB")
            print(f"  - Reduction: {reduction:.1f}%")
        except Exception as e:
            print(f"Failed to process {os.path.basename(path)}: {e}")
            
    print("--- Compression Pipeline Finished ---\n")

def on_select_and_compress(target_entry):
    # Retrieve target size
    target_size_raw = target_entry.get().strip()
    try:
        target_size_kb = int(target_size_raw)
        if target_size_kb <= 0:
            raise ValueError()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid positive integer for Target File Size (KB).")
        return

    # Restrict file types to PDF, JPG, JPEG, and PNG
    filetypes = [
        ("All Supported Files", "*.pdf;*.jpg;*.jpeg;*.png"),
        ("PDF Files (*.pdf)", "*.pdf"),
        ("Image Files (*.jpg;*.jpeg;*.png)", "*.jpg;*.jpeg;*.png")
    ]

    selected_files = filedialog.askopenfilenames(
        title="Select PDF or Image Files",
        filetypes=filetypes
    )

    if not selected_files:
        return

    # Trigger the processing/routing pipeline
    process_files(target_size_kb, selected_files)
    
    # Inform user via dialog
    messagebox.showinfo("Success", f"Dispatched {len(selected_files)} files for processing.\nCheck console for routing output.")

def main():
    root = tk.Tk()
    root.title("Enterprise File Compressor")
    
    # Configure centered window (400x250)
    window_width = 400
    window_height = 250
    
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Calculate position
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False)

    # Style definitions
    bg_color = "#f4f5f7"
    primary_color = "#1e293b" # Dark slate
    accent_color = "#2563eb" # Royal blue
    text_color = "#0f172a"
    button_fg = "#ffffff"
    
    root.configure(bg=bg_color)

    # Title Banner
    title_label = tk.Label(
        root, 
        text="Enterprise File Compressor", 
        font=("Helvetica", 14, "bold"), 
        bg=bg_color, 
        fg=primary_color
    )
    title_label.pack(pady=(20, 10))

    # Subtitle / Info
    info_label = tk.Label(
        root, 
        text="Supported formats: PDF, JPG, JPEG, PNG", 
        font=("Helvetica", 9, "italic"), 
        bg=bg_color, 
        fg="#64748b"
    )
    info_label.pack(pady=(0, 15))

    # Target size input frame
    input_frame = tk.Frame(root, bg=bg_color)
    input_frame.pack(pady=10)

    size_label = tk.Label(
        input_frame, 
        text="Target File Size (KB):", 
        font=("Helvetica", 10), 
        bg=bg_color, 
        fg=text_color
    )
    size_label.pack(side=tk.LEFT, padx=(0, 10))

    target_entry = tk.Entry(
        input_frame, 
        width=10, 
        font=("Helvetica", 10), 
        justify="center"
    )
    target_entry.insert(0, "600")
    target_entry.pack(side=tk.LEFT)

    # Prominent compress button
    compress_button = tk.Button(
        root,
        text="Select Files & Compress",
        font=("Helvetica", 11, "bold"),
        bg=accent_color,
        fg=button_fg,
        activebackground="#1d4ed8",
        activeforeground=button_fg,
        padx=15,
        pady=8,
        relief="flat",
        cursor="hand2",
        command=lambda: on_select_and_compress(target_entry)
    )
    compress_button.pack(pady=(15, 20))

    root.mainloop()

if __name__ == "__main__":
    main()
