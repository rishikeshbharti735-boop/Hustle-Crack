"""
Database Models for Hustle & Crack
Defines Student, TestMark, and Admin tables using Flask-SQLAlchemy.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Student(db.Model):
    """Student model storing personal and academic information."""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), nullable=True)          # ✅ Added roll_number
    father_name = db.Column(db.String(100), nullable=False)
    mother_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    whatsapp = db.Column(db.String(10), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    photo_path = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with TestMark (one-to-many)
    test_marks = db.relationship('TestMark', backref='student', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.student_id}: {self.name}>'


class TestMark(db.Model):
    """Test marks model for storing exam results and PDF-extracted data."""
    __tablename__ = 'test_marks'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    teacher_name = db.Column(db.String(100), nullable=True)        # ✅ Added teacher_name
    subject = db.Column(db.String(50), nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    obtained_marks = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.String(10), nullable=True)
    time_used = db.Column(db.String(20), nullable=True)
    token = db.Column(db.String(20), unique=True, nullable=False, index=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TestMark {self.token}: {self.subject} - {self.obtained_marks}/{self.total_marks}>'


class Admin(db.Model):
    """Admin model for authentication and system management."""
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        """Hash and set the admin password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'


# Optional: Helper function to initialize database (can be called from app.py)
def init_db(app):
    """
    Initialize the database with the Flask app context.
    Creates all tables. Admin creation is handled in app.py.
    """
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")