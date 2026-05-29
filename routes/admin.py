from flask import Blueprint, jsonify, render_template, request
from models import db
from models.appointment_model import Appointment, MedicalReport, Notification
from models.reminder_model import MedicineReminder
from models.user_model import Doctor, Patient, User
from routes import current_user, role_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    stats = {
        "users": User.query.count(),
        "doctors": Doctor.query.count(),
        "patients": Patient.query.count(),
        "appointments": Appointment.query.count(),
        "reports": MedicalReport.query.count(),
        "reminders": MedicineReminder.query.count(),
    }
    doctors = Doctor.query.order_by(Doctor.approved.asc(), Doctor.id.desc()).limit(20).all()
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(12).all()
    return render_template("admin_dashboard.html", user=current_user(), stats=stats, doctors=doctors, appointments=appointments)


@admin_bp.get("/api/users")
@role_required("admin")
def users_api():
    role = request.args.get("role")
    query = User.query
    if role in {"patient", "doctor", "admin"}:
        query = query.filter_by(role=role)
    return jsonify([user.to_dict() for user in query.order_by(User.created_at.desc()).limit(100).all()])


@admin_bp.post("/api/doctors/<int:doctor_id>/approval")
@role_required("admin")
def approve_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    payload = request.get_json() or {}
    doctor.approved = bool(payload.get("approved", True))
    db.session.add(Notification(user_id=doctor.user_id, title="Doctor account reviewed", body=f"Your account is {'approved' if doctor.approved else 'pending review'}.", category="approval"))
    db.session.commit()
    return jsonify({"ok": True, "doctor": doctor.to_card()})


@admin_bp.post("/api/users/<int:user_id>/status")
@role_required("admin")
def user_status(user_id):
    user = User.query.get_or_404(user_id)
    payload = request.get_json() or {}
    user.is_active = bool(payload.get("is_active", True))
    db.session.commit()
    return jsonify({"ok": True, "user": user.to_dict()})
