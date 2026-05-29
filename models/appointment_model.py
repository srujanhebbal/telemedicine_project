from datetime import datetime
from models import db


class Appointment(db.Model):
    __tablename__ = "appointments"
    __table_args__ = (
        db.UniqueConstraint("doctor_id", "scheduled_at", name="uq_doctor_timeslot"),
    )

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    mode = db.Column(db.Enum("video", "audio", "chat"), default="video", nullable=False)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected", "Completed"), default="Pending", nullable=False)
    reason = db.Column(db.String(255))
    payment_status = db.Column(db.Enum("Unpaid", "Paid", "Refunded"), default="Unpaid")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref=db.backref("appointments", lazy=True))
    doctor = db.relationship("Doctor", backref=db.backref("appointments", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "patient": self.patient.user.name,
            "doctor": self.doctor.user.name,
            "doctor_id": self.doctor_id,
            "patient_id": self.patient_id,
            "specialization": self.doctor.specialization,
            "scheduled_at": self.scheduled_at.isoformat(),
            "mode": self.mode,
            "status": self.status,
            "reason": self.reason,
            "payment_status": self.payment_status,
        }


class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    notes = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointment = db.relationship("Appointment", backref=db.backref("prescriptions", lazy=True))


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime)

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])

    def to_dict(self):
        return {
            "id": self.id,
            "appointment_id": self.appointment_id,
            "sender_id": self.sender_id,
            "sender": self.sender.name,
            "receiver_id": self.receiver_id,
            "body": self.body,
            "created_at": self.created_at.strftime("%d %b %Y, %I:%M %p"),
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(40), default="general")
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("notifications", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "category": self.category,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%d %b, %I:%M %p"),
        }


class MedicalReport(db.Model):
    __tablename__ = "medical_reports"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
