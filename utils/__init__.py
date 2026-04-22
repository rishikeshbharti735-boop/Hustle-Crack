"""
utils package for Hustle & Crack
Provides PDF parsing and report generation utilities.
"""

# Import key functions from submodules to make them available directly from utils
from .pdf_parser import extract_exam_data      # Note: function name is extract_exam_data
from .report_gen import generate_remarks, get_grade, calculate_improvement, get_full_analysis

# Optional: define what gets exported with "from utils import *"
__all__ = [
    'extract_exam_data',
    'generate_remarks',
    'get_grade',
    'calculate_improvement',
    'get_full_analysis',
]