import pytesseract
from PIL import Image
import os

# If tesseract is not in your PATH, uncomment and set the following line:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def read_image(path):
    try:
        img=Image.open(path)
        text=pytesseract.image_to_string(img)
        return text
    except pytesseract.TesseractNotFoundError:
        return "Error: Tesseract is not installed or not in your PATH. Please install it from https://github.com/UB-Mannheim/tesseract/wiki"
    except Exception as e:
        return f"Error processing image: {str(e)}"