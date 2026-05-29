from datetime import datetime
from models import db


class MedicineReminder(db.Model):
    __tablename__ = "medicine_reminders"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    medicine_name = db.Column(db.String(140), nullable=False)
    dosage = db.Column(db.String(80), nullable=False)
    reminder_time = db.Column(db.Time, nullable=False)
    schedule = db.Column(db.String(80), default="Daily")
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    taken_count = db.Column(db.Integer, default=0)
    missed_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref=db.backref("medicine_reminders", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "medicine_name": self.medicine_name,
            "dosage": self.dosage,
            "reminder_time": self.reminder_time.strftime("%H:%M"),
            "schedule": self.schedule,
            "taken_count": self.taken_count,
            "missed_count": self.missed_count,
            "is_active": self.is_active,
        }
