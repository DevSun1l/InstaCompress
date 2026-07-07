import fitz  # PyMuPDF
import io
import os
from PIL import Image

def safe_convert_to_rgb(img):
    """
    If the image has an alpha channel (RGBA or LA) or transparency, create a new
    pure white RGB image of the same size, paste the original image onto it
    using its alpha channel as a mask, and return the white-backed RGB image.
    Otherwise, just return img.convert("RGB").
    """
    if img.mode in ("RGBA", "LA") or (img.info and "transparency" in img.info):
        # Create pure white RGB image of the same size
        background = Image.new("RGB", img.size, (255, 255, 255))
        # Convert original to RGBA to ensure we have an alpha channel to use as mask
        rgba_img = img.convert("RGBA")
        # Paste original using alpha as mask
        background.paste(rgba_img, mask=rgba_img.split()[3])
        return background
    else:
        return img.convert("RGB")

def compress_image_stream(img, target_image_kb):
    """
    Compresses the image using a two-phase reduction approach:
    Phase 1: Iteratively lower quality down to 40.
    Phase 2: If quality is 40 or below, iteratively downscale dimensions by 5% until target is met
             or width drops below 150 pixels.
    """
    img = safe_convert_to_rgb(img)
    current_quality = 85
    last_buffer = None
    
    while True:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=current_quality, optimize=True)
        size_kb = buffer.tell() / 1024
        last_buffer = buffer
        
        # If the buffer size is under the target, return it immediately.
        if size_kb <= target_image_kb:
            return buffer
            
        # If it is over the target:
        if current_quality > 40:
            current_quality -= 5
        else:
            # Phase 2 (Dimensions)
            new_width = int(img.width * 0.95)
            new_height = int(img.height * 0.95)
            
            # Safety floor: if new_width < 150, break and return the latest buffer
            if new_width < 150:
                break
                
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
    return last_buffer

def process_pdf(filepath, target_kb, output_folder):
    """
    Processes a PDF by iterating through its pages, extracting unique images,
    compressing them to a portion of the target budget, and replacing them in the PDF.
    Saves the final optimized PDF to output_folder.
    """
    doc = fitz.open(filepath)
    
    # Count unique image xrefs
    unique_xrefs = set()
    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            unique_xrefs.add(xref)
            
    total_images = len(unique_xrefs)
    target_image_kb = target_kb / max(1, total_images)
    
    # Extract, compress and replace images
    processed_xrefs = set()
    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in processed_xrefs:
                continue
                
            try:
                base_image = doc.extract_image(xref)
                if base_image:
                    image_bytes = base_image["image"]
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    
                    # Compress
                    compressed_buf = compress_image_stream(pil_image, target_image_kb)
                    optimized_bytes = compressed_buf.getvalue()
                    
                    # Replace
                    page.replace_image(xref, stream=optimized_bytes)
            except Exception as e:
                print(f"Error compressing image xref {xref} in {filepath}: {e}")
                
            processed_xrefs.add(xref)
            
    # Save optimized PDF
    os.makedirs(output_folder, exist_ok=True)
    filename = os.path.basename(filepath)
    output_path = os.path.join(output_folder, filename)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    
    return output_path

def process_image(filepath, target_kb, output_folder):
    """
    Processes a single standalone image, compressing it to target_kb
    and saving the output bytes as a .jpg to output_folder.
    """
    img = Image.open(filepath)
    buffer = compress_image_stream(img, target_kb)
    
    os.makedirs(output_folder, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    output_path = os.path.join(output_folder, f"{base_name}.jpg")
    
    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())
        
    return output_path
