import tkinter as tk
from tkinter import filedialog, messagebox
import os
from compressor import process_pdf, process_image

# Global state for files
selected_files_list = []

def process_files(target_size_kb, file_paths, output_folder):
    """
    Processes selected PDF and Image files using compressor backend.
    Calculates size reduction and writes output to the specified folder.
    """
    os.makedirs(output_folder, exist_ok=True)

    print(f"\n--- Starting Compression Pipeline ---")
    print(f"Target File Size: {target_size_kb} KB")
    print(f"Output Directory: {output_folder}")
    print(f"Total Files Selected: {len(file_paths)}")
    print("-------------------------------------")

    successful_count = 0
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
            successful_count += 1
        except Exception as e:
            print(f"Failed to process {os.path.basename(path)}: {e}")
            
    print("--- Compression Pipeline Finished ---\n")
    return successful_count

def add_documents(listbox, files_label):
    global selected_files_list
    filetypes = [
        ("All Supported Files", "*.pdf;*.jpg;*.jpeg;*.png"),
        ("PDF Files (*.pdf)", "*.pdf"),
        ("Image Files (*.jpg;*.jpeg;*.png)", "*.jpg;*.jpeg;*.png")
    ]
    files = filedialog.askopenfilenames(
        title="Select PDF or Image Files",
        filetypes=filetypes
    )
    if files:
        for f in files:
            if f not in selected_files_list:
                selected_files_list.append(f)
                listbox.insert(tk.END, os.path.basename(f))
        files_label.config(text=f"Files added: {len(selected_files_list)}")

def browse_output_folder(output_entry):
    folder = filedialog.askdirectory(title="Select Output Save Location")
    if folder:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, folder)

def start_compression(target_entry, output_entry, listbox, files_label):
    global selected_files_list
    if not selected_files_list:
        messagebox.showwarning("No Files", "Please add one or more files to compress first.")
        return

    output_dir = output_entry.get().strip()
    if not output_dir:
        messagebox.showwarning("No Output Path", "Please select a valid output save location.")
        return

    target_size_raw = target_entry.get().strip()
    try:
        target_size_kb = int(target_size_raw)
        if target_size_kb <= 0:
            raise ValueError()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid positive integer for Target File Size (KB).")
        return

    # Trigger processing
    success_count = process_files(target_size_kb, selected_files_list, output_dir)
    
    # Notify user
    messagebox.showinfo("Finished", f"Successfully compressed {success_count} of {len(selected_files_list)} files.\nCheck console for details.")
    
    # Clear selections after processing
    selected_files_list.clear()
    listbox.delete(0, tk.END)
    files_label.config(text="Files added: 0")

def main():
    root = tk.Tk()
    root.title("Enterprise File Compressor")
    
    # Configure centered window (450x420 to fit all new layouts nicely)
    window_width = 450
    window_height = 420
    
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
    success_color = "#10b981" # Emerald green for Start Compress
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
    title_label.pack(pady=(15, 5))

    # Add Documents Button & Count Label
    files_frame = tk.Frame(root, bg=bg_color)
    files_frame.pack(fill=tk.X, padx=25, pady=5)
    
    add_btn = tk.Button(
        files_frame,
        text="Add Documents",
        font=("Helvetica", 10, "bold"),
        bg="#475569", # Slate
        fg=button_fg,
        activebackground="#334155",
        activeforeground=button_fg,
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=5,
        command=lambda: add_documents(files_listbox, files_count_label)
    )
    add_btn.pack(side=tk.LEFT)

    files_count_label = tk.Label(
        files_frame, 
        text="Files added: 0", 
        font=("Helvetica", 10, "bold"), 
        bg=bg_color, 
        fg="#64748b"
    )
    files_count_label.pack(side=tk.RIGHT, padx=10)

    # Listbox to show selected files
    listbox_frame = tk.Frame(root, bg=bg_color)
    listbox_frame.pack(fill=tk.BOTH, padx=25, pady=5)
    
    scrollbar = tk.Scrollbar(listbox_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    files_listbox = tk.Listbox(
        listbox_frame, 
        height=5, 
        font=("Helvetica", 9), 
        bd=1, 
        relief="solid",
        yscrollcommand=scrollbar.set
    )
    files_listbox.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=files_listbox.yview)

    # Output Folder Selection Frame
    output_frame = tk.Frame(root, bg=bg_color)
    output_frame.pack(fill=tk.X, padx=25, pady=10)

    output_label = tk.Label(
        output_frame,
        text="Output Folder:",
        font=("Helvetica", 9, "bold"),
        bg=bg_color,
        fg=text_color
    )
    output_label.pack(anchor="w")

    output_inner = tk.Frame(output_frame, bg=bg_color)
    output_inner.pack(fill=tk.X, pady=(2, 0))

    default_output = os.path.join(os.path.expanduser("~"), "Desktop", "Compressed_Files")
    output_entry = tk.Entry(
        output_inner, 
        font=("Helvetica", 9), 
        bd=1, 
        relief="solid"
    )
    output_entry.insert(0, default_output)
    output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    browse_btn = tk.Button(
        output_inner,
        text="Browse...",
        font=("Helvetica", 9),
        bg="#e2e8f0",
        fg=text_color,
        activebackground="#cbd5e1",
        relief="flat",
        cursor="hand2",
        command=lambda: browse_output_folder(output_entry)
    )
    browse_btn.pack(side=tk.RIGHT)

    # Target Size input frame
    input_frame = tk.Frame(root, bg=bg_color)
    input_frame.pack(fill=tk.X, padx=25, pady=5)

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
        justify="center",
        bd=1,
        relief="solid"
    )
    target_entry.insert(0, "600")
    target_entry.pack(side=tk.LEFT)

    # Prominent Start Compress Button
    compress_button = tk.Button(
        root,
        text="Start Compress",
        font=("Helvetica", 12, "bold"),
        bg=success_color,
        fg=button_fg,
        activebackground="#059669",
        activeforeground=button_fg,
        padx=20,
        pady=8,
        relief="flat",
        cursor="hand2",
        command=lambda: start_compression(target_entry, output_entry, files_listbox, files_count_label)
    )
    compress_button.pack(pady=(15, 10))

    root.mainloop()

if __name__ == "__main__":
    main()
