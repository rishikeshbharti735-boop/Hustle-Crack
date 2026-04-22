"""
Report Generation Module for Hustle & Crack
Automated performance analysis, remarks, grading, and subject insights.
"""

from typing import Dict, List, Union


def generate_remarks(percentage: float, accuracy: float = None) -> str:
    """
    Generate a personalized remark based on percentage and optional accuracy.
    
    Args:
        percentage (float): Student's overall percentage (0-100).
        accuracy (float, optional): Accuracy percentage (0-100). Defaults to None.
        
    Returns:
        str: Motivational or corrective remark.
    """
    if percentage >= 85:
        return "Excellent! Dominating the subject. Keep setting higher goals!"
    elif percentage >= 70:
        return "Good job! Aim for the top spot with consistent revision."
    elif percentage >= 50:
        return "Satisfactory. Focus on weak areas to boost your score."
    else:
        return "Needs focus. Revision required in specific topics. Seek teacher guidance."


def calculate_improvement(current_marks: float, previous_marks: float) -> str:
    """
    Calculate percentage improvement between two marks.
    
    Args:
        current_marks (float): Latest marks/percentage.
        previous_marks (float): Previous marks/percentage.
        
    Returns:
        str: Formatted improvement message, e.g., '+5% Improvement' or '-3% Down'.
    """
    if previous_marks == 0:
        return "No previous data available"
    
    diff = current_marks - previous_marks
    percent_change = (diff / previous_marks) * 100 if previous_marks != 0 else 0
    
    if diff > 0:
        return f"+{percent_change:.1f}% Improvement"
    elif diff < 0:
        return f"{percent_change:.1f}% Down"
    else:
        return "No change from previous assessment"


def get_grade(percentage: float) -> str:
    """
    Convert percentage to letter grade.
    
    Args:
        percentage (float): Student's percentage (0-100).
        
    Returns:
        str: Grade (A+, A, B+, B, C, D, F).
    """
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B+"
    elif percentage >= 60:
        return "B"
    elif percentage >= 50:
        return "C"
    elif percentage >= 40:
        return "D"
    else:
        return "F"


def suggest_weak_subject(subject_marks: Dict[str, float]) -> str:
    """
    Suggest which subject needs more attention based on lowest marks.
    
    Args:
        subject_marks (dict): Dictionary mapping subject names to marks/percentages.
                              Example: {'Mathematics': 72, 'Physics': 45, 'Chemistry': 68}
        
    Returns:
        str: Suggestion message indicating the weakest subject.
    """
    if not subject_marks:
        return "No subject data available to analyze."
    
    # Find subject with lowest marks
    weakest_subject = min(subject_marks, key=subject_marks.get)
    lowest_mark = subject_marks[weakest_subject]
    
    return f"Needs more attention in {weakest_subject} (score: {lowest_mark}%). Focused revision recommended."


# Optional: Combined analytics function for a student
def get_full_analysis(percentage: float, accuracy: float = None, 
                      previous_marks: float = None, 
                      subject_marks: Dict[str, float] = None) -> Dict[str, str]:
    """
    Generate complete analysis including remark, grade, improvement, and weak subject.
    
    Args:
        percentage (float): Current overall percentage.
        accuracy (float, optional): Accuracy percentage.
        previous_marks (float, optional): Previous assessment marks.
        subject_marks (dict, optional): Subject-wise marks.
        
    Returns:
        dict: Dictionary containing remark, grade, improvement, weak_subject_suggestion.
    """
    analysis = {
        "remark": generate_remarks(percentage, accuracy),
        "grade": get_grade(percentage)
    }
    
    if previous_marks is not None:
        analysis["improvement"] = calculate_improvement(percentage, previous_marks)
    else:
        analysis["improvement"] = "No previous data"
    
    if subject_marks:
        analysis["weak_subject_suggestion"] = suggest_weak_subject(subject_marks)
    else:
        analysis["weak_subject_suggestion"] = "No subject-wise data available"
    
    return analysis


# Example usage (for testing)
if __name__ == "__main__":
    # Test remark function
    print(generate_remarks(88))          # Excellent...
    print(generate_remarks(45))          # Needs focus...
    
    # Test improvement
    print(calculate_improvement(75, 70)) # +7.1% Improvement
    
    # Test grade
    print(get_grade(85))                 # A
    
    # Test weak subject suggestion
    marks = {"Math": 92, "Physics": 48, "Chemistry": 71}
    print(suggest_weak_subject(marks))   # Needs more attention in Physics...
    
    # Full analysis
    full = get_full_analysis(78, accuracy=82, previous_marks=70, subject_marks=marks)
    print(full)