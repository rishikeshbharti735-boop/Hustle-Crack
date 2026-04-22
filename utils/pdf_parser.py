"""
PDF Parser Module for Hustle & Crack
Extracts exam results from FIRST PAGE of PDF using exact pattern matching.
"""

import re
import os
from typing import Dict, Union

try:
    import PyPDF2
except ImportError:
    raise ImportError("PyPDF2 is required. Install with: pip install PyPDF2")


def extract_exam_data(pdf_path: str) -> Dict[str, Union[str, None]]:
    """
    Extract exam data from FIRST PAGE of a PDF file.
    Returns dict with keys: marks_obtained, accuracy, time_used, grade, error.
    """
    result = {
        'marks_obtained': None,
        'accuracy': None,
        'time_used': None,
        'grade': None,
        'error': None
    }

    if not os.path.exists(pdf_path):
        result['error'] = f"File not found: {pdf_path}"
        return result

    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if len(reader.pages) == 0:
                result['error'] = "PDF has no pages"
                return result

            # Extract ONLY FIRST PAGE
            first_page = reader.pages[0]
            page_text = first_page.extract_text()
            if not page_text:
                result['error'] = "No text extracted from first page"
                return result

            # ========== 1. Extract MARKS OBTAINED ==========
            # Pattern: "Marks Obtained 34/50"
            marks_match = re.search(r'Marks\s+Obtained\s+(\d+)/(\d+)', page_text, re.IGNORECASE)
            if marks_match:
                result['marks_obtained'] = f"{marks_match.group(1)}/{marks_match.group(2)}"
            else:
                # Fallback: find any "number/number" in the text
                fallback = re.search(r'(\d+)/(\d+)', page_text)
                if fallback:
                    result['marks_obtained'] = f"{fallback.group(1)}/{fallback.group(2)}"

            # ========== 2. Extract ACCURACY ==========
            # Pattern: "Accuracy 69%" or "Accuracy: 69%"
            acc_match = re.search(r'Accuracy\s+(\d+)%', page_text, re.IGNORECASE)
            if acc_match:
                result['accuracy'] = f"{acc_match.group(1)}%"
            else:
                # Fallback: find any percentage not equal to 100 (total QS percentage might be 100)
                percent_match = re.findall(r'(\d+)%', page_text)
                for p in percent_match:
                    if int(p) != 100:
                        result['accuracy'] = f"{p}%"
                        break

            # ========== 3. Extract TIME USED ==========
            # Pattern: "Time Used 19m 12s"
            time_match = re.search(r'Time\s+Used\s+(\d+)m\s+(\d+)s', page_text, re.IGNORECASE)
            if time_match:
                result['time_used'] = f"{time_match.group(1)}m {time_match.group(2)}s"
            else:
                # Fallback: find "Xm Ys"
                fallback = re.search(r'(\d+)m\s+(\d+)s', page_text)
                if fallback:
                    result['time_used'] = f"{fallback.group(1)}m {fallback.group(2)}s"

            # ========== 4. Extract GRADE ==========
            # Pattern: "Grade B" (single letter after "Grade")
            grade_match = re.search(r'Grade\s+([A-D][+-]?)', page_text, re.IGNORECASE)
            if grade_match:
                result['grade'] = grade_match.group(1).upper()
            else:
                # Look for standalone letter A, B, C, D near the end of text
                letter_match = re.search(r'\b([A-D])\b', page_text[-300:])
                if letter_match:
                    result['grade'] = letter_match.group(1)

            # If nothing found, set error
            if all(v is None for v in [result['marks_obtained'], result['accuracy'], 
                                        result['time_used'], result['grade']]):
                result['error'] = "Could not extract data from PDF. Please check format."

            return result

    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        return result


if __name__ == "__main__":
    # Quick test (create a sample file)
    test_pdf = "sample_exam.pdf"
    if os.path.exists(test_pdf):
        data = extract_exam_data(test_pdf)
        print("Extracted Data:")
        for k, v in data.items():
            print(f"  {k}: {v}")
    else:
        print("No sample PDF found. Place a test PDF named 'sample_exam.pdf' in this folder.")