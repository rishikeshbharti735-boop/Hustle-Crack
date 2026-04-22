"""
Hustle & Crack - Main Flask Application
Handles routes, database operations, file uploads, PDF parsing, and report generation.
"""

import os
import uuid
import random
import string
import io
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Import database models and utilities
from models import db, Student, TestMark, Admin
from utils.pdf_parser import extract_exam_data
from utils.report_gen import get_full_analysis, generate_remarks, get_grade, calculate_improvement

# Excel & PDF export libraries
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# ---------------------------
# App Configuration
# ---------------------------
app = Flask(__name__)

# Fix: Absolute path for SQLite database (prevents deletion on Render)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'hustle-crack-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'hustle_crack.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session timeout

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

# Initialize database
db.init_app(app)

# Create upload directories if they don't exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'temp_pdf'), exist_ok=True)


# ---------------------------
# Helper Functions
# ---------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_missing_columns():
    """Add missing columns to existing tables without data loss"""
    import sqlite3
    db_path = os.path.join(basedir, 'hustle_crack.db')
    
    if not os.path.exists(db_path):
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check students table
    cursor.execute("PRAGMA table_info(students)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    
    if 'roll_number' not in existing_cols:
        print("✅ Adding 'roll_number' column to students...")
        cursor.execute("ALTER TABLE students ADD COLUMN roll_number VARCHAR(20)")
    
    # Check test_marks table
    cursor.execute("PRAGMA table_info(test_marks)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    
    if 'teacher_name' not in existing_cols:
        print("✅ Adding 'teacher_name' column to test_marks...")
        cursor.execute("ALTER TABLE test_marks ADD COLUMN teacher_name VARCHAR(100)")
    
    conn.commit()
    conn.close()


def generate_student_id():
    """Generate sequential student ID like HC-2026-001"""
    current_year = datetime.now().year
    last_student = Student.query.order_by(Student.id.desc()).first()
    if last_student:
        parts = last_student.student_id.split('-')
        if len(parts) == 3 and parts[0] == 'HC' and parts[1] == str(current_year):
            last_num = int(parts[2])
            new_num = last_num + 1
        else:
            new_num = 1
    else:
        new_num = 1
    return f"HC-{current_year}-{new_num:03d}"


def generate_token():
    """Generate a unique token for test entries (e.g., TK-78X92)"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=6))
    return f"TK-{random_part}"


def admin_required(f):
    """Decorator to protect admin routes - redirects to login if not authenticated"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login as admin first.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------
# Routes: Portal & Home
# ---------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/portal-choice')
def portal_choice():
    return render_template('portal_choice.html')


# ---------------------------
# Student Dashboard & Actions
# ---------------------------
@app.route('/student/dashboard')
def student_dashboard():
    students = Student.query.all()
    return render_template('student/dashboard.html', students=students)


@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form.get('fullName')
        class_name = request.form.get('classSelect')
        roll_number = request.form.get('rollNumber')
        father_name = request.form.get('fatherName')
        mother_name = request.form.get('motherName')
        phone = request.form.get('phone')
        whatsapp = request.form.get('whatsapp')
        
        photo = request.files.get('photoUpload')
        photo_path = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{photo.filename}")
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], 'photos', filename))
            photo_path = f"uploads/photos/{filename}"
        
        student_id = generate_student_id()
        
        new_student = Student(
            student_id=student_id,
            name=name,
            roll_number=roll_number,
            father_name=father_name,
            mother_name=mother_name,
            phone=phone,
            whatsapp=whatsapp,
            class_name=class_name,
            photo_path=photo_path
        )
        db.session.add(new_student)
        db.session.commit()
        
        flash(f'Registration successful! Student ID: {student_id}', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student/register.html')


@app.route('/student/marks-entry', methods=['GET', 'POST'])
def marks_entry():
    if request.method == 'POST':
        student_id = request.form.get('studentRoll')
        teacher_name = request.form.get('teacherName')
        subject = request.form.get('subject')
        total_marks = float(request.form.get('totalMarks'))
        obtained_marks = float(request.form.get('obtainedMarks'))
        
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            flash('Student ID not found. Please register first.', 'error')
            return redirect(url_for('marks_entry'))
        
        accuracy = (obtained_marks / total_marks) * 100 if total_marks > 0 else 0
        accuracy_str = f"{accuracy:.1f}%"
        token = generate_token()
        
        test_mark = TestMark(
            student_id=student_id,
            teacher_name=teacher_name,
            subject=subject,
            total_marks=total_marks,
            obtained_marks=obtained_marks,
            accuracy=accuracy_str,
            token=token
        )
        db.session.add(test_mark)
        db.session.commit()
        
        flash(f'Marks saved successfully! Token: {token}', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student/marks_entry.html')


@app.route('/student/pdf-upload', methods=['GET', 'POST'])
def pdf_upload():
    if request.method == 'POST':
        student_id = request.form.get('studentId')
        pdf_file = request.files.get('pdfFile')
        
        if not pdf_file or not allowed_file(pdf_file.filename):
            flash('Please upload a valid PDF file.', 'error')
            return redirect(url_for('pdf_upload'))
        
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            flash('Student ID not found.', 'error')
            return redirect(url_for('pdf_upload'))
        
        temp_filename = secure_filename(f"{uuid.uuid4().hex}.pdf")
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_pdf', temp_filename)
        pdf_file.save(temp_path)
        
        try:
            extracted = extract_exam_data(temp_path)
            if extracted.get('error'):
                flash(f'PDF parsing error: {extracted["error"]}', 'error')
                return redirect(url_for('pdf_upload'))
            
            marks_obtained = extracted.get('marks_obtained')
            accuracy = extracted.get('accuracy')
            time_used = extracted.get('time_used')
            
            total_marks = None
            obtained_marks = None
            if marks_obtained and '/' in marks_obtained:
                parts = marks_obtained.split('/')
                obtained_marks = float(parts[0])
                total_marks = float(parts[1])
            
            subject = "Exam"
            token = generate_token()
            
            test_mark = TestMark(
                student_id=student_id,
                subject=subject,
                total_marks=total_marks or 0,
                obtained_marks=obtained_marks or 0,
                accuracy=accuracy or "N/A",
                time_used=time_used or "N/A",
                token=token
            )
            db.session.add(test_mark)
            db.session.commit()
            
            flash(f'PDF processed successfully! Token: {token}', 'success')
        except Exception as e:
            flash(f'Error processing PDF: {str(e)}', 'error')
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return redirect(url_for('student_dashboard'))
    
    return render_template('student/pdf_upload.html')


@app.route('/student/report-card')
def report_card():
    student_id = request.args.get('student_id')
    if not student_id:
        flash('Please provide student ID', 'error')
        return redirect(url_for('student_dashboard'))
    
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('student_dashboard'))
    
    test_marks = TestMark.query.filter_by(student_id=student_id).order_by(TestMark.date_added.desc()).all()
    
    percentages = []
    for tm in test_marks:
        if tm.total_marks > 0:
            pct = (tm.obtained_marks / tm.total_marks) * 100
            percentages.append(pct)
    overall_percentage = sum(percentages) / len(percentages) if percentages else 0
    
    analysis = get_full_analysis(
        percentage=overall_percentage,
        previous_marks=None,
        subject_marks={tm.subject: (tm.obtained_marks/tm.total_marks)*100 if tm.total_marks>0 else 0 for tm in test_marks}
    )
    
    test_labels = [f"Test {i+1}" for i in range(len(test_marks))]
    test_scores = [(tm.obtained_marks/tm.total_marks)*100 if tm.total_marks>0 else 0 for tm in test_marks]
    
    return render_template('student/report_card.html', 
                          student=student,
                          test_marks=test_marks,
                          overall_percentage=overall_percentage,
                          analysis=analysis,
                          test_labels=test_labels,
                          test_scores=test_scores)


# ---------------------------
# Teacher Dashboard
# ---------------------------
@app.route('/teacher/dashboard')
def teacher_dashboard():
    students = Student.query.all()
    student_performance = []
    for s in students:
        latest_mark = TestMark.query.filter_by(student_id=s.student_id).order_by(TestMark.date_added.desc()).first()
        if latest_mark:
            percentage = (latest_mark.obtained_marks / latest_mark.total_marks) * 100 if latest_mark.total_marks > 0 else 0
            remark = generate_remarks(percentage)
        else:
            percentage = 0
            remark = "No data"
        student_performance.append({
            'student': s,
            'percentage': percentage,
            'remark': remark
        })
    return render_template('teacher/dashboard.html', students=student_performance)


# ---------------------------
# Admin Authentication & Dashboard
# ---------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # If already logged in, redirect to dashboard
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session.permanent = True
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Logged out.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_students = Student.query.count()
    total_tests = TestMark.query.count()
    avg_performance = db.session.query(db.func.avg((TestMark.obtained_marks / TestMark.total_marks) * 100)).scalar() or 0
    pending_reports = Student.query.filter(~Student.test_marks.any()).count()
    
    students = Student.query.all()
    student_data = []
    for s in students:
        latest = TestMark.query.filter_by(student_id=s.student_id).order_by(TestMark.date_added.desc()).first()
        if latest:
            pct = (latest.obtained_marks / latest.total_marks) * 100 if latest.total_marks > 0 else 0
            grade = get_grade(pct)
            remark = generate_remarks(pct)
        else:
            pct = 0
            grade = "N/A"
            remark = "No data"
        student_data.append({
            'id': s.student_id,
            'name': s.name,
            'class': s.class_name,
            'percentage': round(pct, 1),
            'grade': grade,
            'remark': remark,
            'photo': s.photo_path
        })
    
    return render_template('admin/dashboard.html',
                          total_students=total_students,
                          total_tests=total_tests,
                          avg_performance=round(avg_performance, 1),
                          pending_reports=pending_reports,
                          students=student_data)


@app.route('/admin/edit-marks', methods=['POST'])
@admin_required
def edit_marks():
    data = request.get_json()
    student_id = data.get('student_id')
    new_percentage = float(data.get('percentage'))
    
    test_mark = TestMark.query.filter_by(student_id=student_id).order_by(TestMark.date_added.desc()).first()
    if test_mark:
        test_mark.obtained_marks = (new_percentage / 100) * test_mark.total_marks
        db.session.commit()
        return jsonify({'success': True, 'remark': generate_remarks(new_percentage)})
    return jsonify({'success': False, 'error': 'No test found'}), 404


# ---------------------------
# Export Endpoints (Excel & PDF)
# ---------------------------
@app.route('/admin/export/excel')
@admin_required
def export_excel():
    """Export all student data to Excel file"""
    students = Student.query.all()
    data = []
    for s in students:
        latest = TestMark.query.filter_by(student_id=s.student_id).order_by(TestMark.date_added.desc()).first()
        if latest:
            pct = (latest.obtained_marks / latest.total_marks) * 100 if latest.total_marks > 0 else 0
            grade = get_grade(pct)
            remark = generate_remarks(pct)
        else:
            pct = 0
            grade = "N/A"
            remark = "No data"
        data.append({
            'Student ID': s.student_id,
            'Name': s.name,
            'Roll Number': s.roll_number,
            'Class': s.class_name,
            'Father\'s Name': s.father_name,
            'Mother\'s Name': s.mother_name,
            'Phone': s.phone,
            'WhatsApp': s.whatsapp,
            'Overall Percentage': round(pct, 1),
            'Grade': grade,
            'Remark': remark,
            'Registered On': s.created_at.strftime('%Y-%m-%d') if s.created_at else ''
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Students', index=False)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=hustle_crack_students_{datetime.now().strftime("%Y%m%d")}.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response


@app.route('/admin/export/pdf')
@admin_required
def export_pdf():
    """Export student summary to PDF"""
    students = Student.query.all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, textColor=colors.HexColor('#C9A84C'))
    elements.append(Paragraph("Hustle & Crack - Student Performance Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    table_data = [['Student ID', 'Name', 'Class', 'Overall %', 'Grade', 'Remark']]
    for s in students:
        latest = TestMark.query.filter_by(student_id=s.student_id).order_by(TestMark.date_added.desc()).first()
        if latest:
            pct = (latest.obtained_marks / latest.total_marks) * 100 if latest.total_marks > 0 else 0
            grade = get_grade(pct)
            remark = generate_remarks(pct)
        else:
            pct = 0
            grade = "N/A"
            remark = "No data"
        table_data.append([
            s.student_id, s.name, s.class_name, f"{round(pct,1)}%", grade, remark
        ])
    
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#C9A84C')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#1A1A22')),
        ('TEXTCOLOR', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#7A5F28')),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=hustle_crack_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response


# ---------------------------
# Error Handlers
# ---------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# ---------------------------
# Run App
# ---------------------------
if __name__ == '__main__':
    with app.app_context():
        add_missing_columns()
        db.create_all()
        if not Admin.query.filter_by(username='admin').first():
            default_admin = Admin(username='admin')
            default_admin.set_password('7474')
            db.session.add(default_admin)
            db.session.commit()
            print("Default admin created: admin / 7474")
    app.run(debug=True, host='0.0.0.0', port=5001)