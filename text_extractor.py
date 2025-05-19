import os
import sys
import PyPDF2
import docx

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_txt(file_path):
    """Extract text from a TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try another encoding if UTF-8 fails
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            print(f"Error extracting text from TXT with latin-1 encoding: {e}")
            return ""
    except Exception as e:
        print(f"Error extracting text from TXT: {e}")
        return ""

def extract_text(file_path):
    """Extract text from a file based on its extension"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return ""
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    elif file_extension == '.txt':
        return extract_text_from_txt(file_path)
    else:
        print(f"Unsupported file format: {file_extension}")
        return ""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python text_extractor.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    text = extract_text(file_path)
    
    if text:
        print("\n--- Extracted Text ---\n")
        print(text[:2000])  # Print first 2000 characters
        print("\n--- End of Preview ---\n")
        print(f"Total characters extracted: {len(text)}")
        
        # Option to save the extracted text
        save_option = input("Do you want to save the extracted text to a file? (y/n): ")
        if save_option.lower() == 'y':
            output_file = os.path.splitext(file_path)[0] + "_extracted.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Text saved to: {output_file}")
    else:
        print("No text was extracted from the file.")