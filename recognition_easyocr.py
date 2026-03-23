# recognition_easyocr.py
import easyocr

# Initialize OCR reader once (for English)
reader = easyocr.Reader(['en'])

def extract_text(image_path):
    try:
        results = reader.readtext(image_path, detail=0, paragraph=True)
        text = " ".join(results)
        return text.strip()
    except Exception as e:
        print(f"[ERROR] OCR extraction failed: {e}")
        return ""
