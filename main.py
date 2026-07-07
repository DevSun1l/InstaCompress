import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from compressor import process_pdf, process_image

# Global state for files
selected_files_list = []

def process_files_sync(target_size_kb, file_paths, output_folder):
    """
    Synchronous processing function (still printed to console).
    """
    os.makedirs(output_folder, exist_ok=True)
    successful_count = 0
    for path in file_paths:
        if not os.path.exists(path):
            continue
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".pdf":
                process_pdf(path, target_size_kb, output_folder)
            elif ext in (".jpg", ".jpeg", ".png"):
                process_image(path, target_size_kb, output_folder)
            successful_count += 1
        except Exception as e:
            print(f"Error: {e}")
    return successful_count

def mark_file_complete(listbox, index, filename):
    listbox.delete(index)
    listbox.insert(index, f"✓ {filename}")
    listbox.itemconfig(index, {'fg': '#10b981'})  # Green color

def mark_file_failed(listbox, index, filename):
    listbox.delete(index)
    listbox.insert(index, f"✗ {filename} (Failed)")
    listbox.itemconfig(index, {'fg': '#ef4444'})  # Red color

def finish_compression(progress_win, successful_count, total_files):
    progress_win.destroy()
    messagebox.showinfo("Finished", f"Successfully compressed {successful_count} of {total_files} files.\nCheck console for details.")

def compress_worker(root, target_size_kb, file_paths, output_folder, listbox, progress_label, progress_bar, progress_win):
    os.makedirs(output_folder, exist_ok=True)
    total_files = len(file_paths)
    
    print(f"\n--- Starting Compression Pipeline ---")
    print(f"Target File Size: {target_size_kb} KB")
    print(f"Output Directory: {output_folder}")
    print(f"Total Files Selected: {total_files}")
    print("-------------------------------------")

    successful_count = 0
    
    for i, path in enumerate(file_paths):
        filename = os.path.basename(path)
        
        # Update progress screen label and progress bar
        msg = f"Compressing {i+1} of {total_files}:\n{filename}"
        root.after(0, lambda m=msg: progress_label.config(text=m))
        root.after(0, lambda val=int((i / total_files) * 100): progress_bar.config(value=val))
        
        if not os.path.exists(path):
            print(f"File not found: {path}")
            root.after(0, lambda idx=i, fn=filename: mark_file_failed(listbox, idx, fn))
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
                root.after(0, lambda idx=i, fn=filename: mark_file_failed(listbox, idx, fn))
                continue
            
            compressed_size = os.path.getsize(output_path)
            reduction = (1 - compressed_size / orig_size) * 100 if orig_size > 0 else 0
            
            print(f"Processed: {filename}")
            print(f"  - Original Size: {orig_size / 1024:.2f} KB")
            print(f"  - Compressed Size: {compressed_size / 1024:.2f} KB")
            print(f"  - Reduction: {reduction:.1f}%")
            successful_count += 1
            
            # Show a green checkmark next to the file when done
            root.after(0, lambda idx=i, fn=filename: mark_file_complete(listbox, idx, fn))
            
        except Exception as e:
            print(f"Failed to process {filename}: {e}")
            root.after(0, lambda idx=i, fn=filename: mark_file_failed(listbox, idx, fn))
            
    # Complete the progress bar and finish
    root.after(0, lambda: progress_bar.config(value=100))
    root.after(0, lambda: progress_label.config(text="Finished compression!"))
    root.after(500, lambda: finish_compression(progress_win, successful_count, total_files))
    
    print("--- Compression Pipeline Finished ---\n")

def clear_completed_from_listbox(listbox, files_label):
    global selected_files_list
    # Check if we have completed marks in the listbox. If so, clear the whole queue.
    has_completed = False
    for i in range(listbox.size()):
        text = listbox.get(i)
        if text.startswith("✓") or text.startswith("✗"):
            has_completed = True
            break
    if has_completed:
        listbox.delete(0, tk.END)
        selected_files_list.clear()
        files_label.config(text="Files added: 0")

def add_documents(listbox, files_label):
    global selected_files_list
    
    # If the list contains completed items from the last run, clear them first
    clear_completed_from_listbox(listbox, files_label)
    
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

def create_progress_window(parent, total_files):
    progress_win = tk.Toplevel(parent)
    progress_win.title("Compressing...")
    
    # Modal behavior
    progress_win.transient(parent)
    progress_win.grab_set()
    
    # Configure size and position centered to parent
    width = 340
    height = 140
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()
    
    x = parent_x + (parent_w - width) // 2
    y = parent_y + (parent_h - height) // 2
    progress_win.geometry(f"{width}x{height}+{x}+{y}")
    progress_win.resizable(False, False)
    progress_win.configure(bg="#f4f5f7")
    
    # Disable closing the progress window directly
    progress_win.protocol("WM_DELETE_WINDOW", lambda: None)
    
    # Label
    progress_label = tk.Label(
        progress_win,
        text="Initializing compression...",
        font=("Helvetica", 10),
        bg="#f4f5f7",
        fg="#0f172a",
        justify="center"
    )
    progress_label.pack(pady=(20, 10), fill=tk.X, padx=15)
    
    # Progress Bar
    progress_bar = ttk.Progressbar(
        progress_win,
        orient="horizontal",
        length=280,
        mode="determinate"
    )
    progress_bar.pack(pady=10)
    
    return progress_win, progress_label, progress_bar

def start_compression(root, target_entry, output_entry, listbox, files_label):
    global selected_files_list
    
    # Ensure there are files queued
    if not selected_files_list:
        messagebox.showwarning("No Files", "Please add one or more files to compress first.")
        return

    # If the listbox already contains checkmarks or cross marks (already processed), warn user to add new ones
    has_unprocessed = False
    for i in range(listbox.size()):
        text = listbox.get(i)
        if not (text.startswith("✓") or text.startswith("✗")):
            has_unprocessed = True
            break
            
    if not has_unprocessed:
        messagebox.showwarning("Already Compressed", "All queued files have already been processed. Add new documents to run again.")
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

    # Create progress window
    progress_win, progress_label, progress_bar = create_progress_window(root, len(selected_files_list))
    
    # Start compression in background thread to keep UI responsive
    t = threading.Thread(
        target=compress_worker,
        args=(root, target_size_kb, list(selected_files_list), output_dir, listbox, progress_label, progress_bar, progress_win)
    )
    t.daemon = True
    t.start()

def main():
    root = tk.Tk()
    root.title("Enterprise File Compressor")
    
    # Configure centered window
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
        command=lambda: start_compression(root, target_entry, output_entry, files_listbox, files_count_label)
    )
    compress_button.pack(pady=(15, 10))

    root.mainloop()

if __name__ == "__main__":
    main()
