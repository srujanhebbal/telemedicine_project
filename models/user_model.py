from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from models import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("patient", "doctor", "admin"), nullable=False, default="patient")
    phone = db.Column(db.String(25))
    avatar = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor = db.relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    blood_group = db.Column(db.String(8))
    address = db.Column(db.String(255))
    allergies = db.Column(db.Text)
    conditions = db.Column(db.Text)

    user = db.relationship("User", back_populates="patient")


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization = db.Column(db.String(120), nullable=False, default="General Medicine")
    qualification = db.Column(db.String(160))
    experience_years = db.Column(db.Integer, default=0)
    consultation_fee = db.Column(db.Numeric(10, 2), default=0)
    bio = db.Column(db.Text)
    availability = db.Column(db.JSON)
    approved = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Numeric(3, 2), default=4.8)

    user = db.relationship("User", back_populates="doctor")

    def to_card(self):
        return {
            "id": self.id,
            "name": self.user.name,
            "email": self.user.email,
            "specialization": self.specialization,
            "qualification": self.qualification,
            "experience_years": self.experience_years,
            "consultation_fee": float(self.consultation_fee or 0),
            "approved": self.approved,
            "rating": float(self.rating or 0),
            "bio": self.bio,
        }
