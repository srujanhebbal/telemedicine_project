import os
from datetime import datetime
from flask import Blueprint, current_app, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from models import db
from models.appointment_model import Appointment, MedicalReport, Message, Notification, Prescription
from models.reminder_model import MedicineReminder
from models.user_model import Doctor
from routes import current_user, role_required


patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


@patient_bp.route("/dashboard")
@role_required("patient")
def dashboard():
    user = current_user()
    doctors = Doctor.query.filter_by(approved=True).limit(6).all()
    appointments = Appointment.query.filter_by(patient_id=user.patient.id).order_by(Appointment.scheduled_at.desc()).limit(8).all()
    reminders = MedicineReminder.query.filter_by(patient_id=user.patient.id, is_active=True).limit(5).all()
    return render_template("patient_dashboard.html", user=user, doctors=doctors, appointments=appointments, reminders=reminders)


@patient_bp.route("/appointments")
@role_required("patient")
def appointments_page():
    return render_template("appointment.html", user=current_user(), doctors=Doctor.query.filter_by(approved=True).all())


@patient_bp.route("/chat/<int:appointment_id>")
@role_required("patient")
def chat_page(appointment_id):
    return render_template("chat.html", user=current_user(), appointment_id=appointment_id)


@patient_bp.route("/consultation/<int:appointment_id>")
@role_required("patient")
def consultation_page(appointment_id):
    return render_template("video_consultation.html", user=current_user(), appointment_id=appointment_id)


@patient_bp.route("/reminders")
@role_required("patient")
def reminder_page():
    return render_template("reminder.html", user=current_user())


@patient_bp.route("/profile")
@role_required("patient")
def profile_page():
    return render_template("profile.html", user=current_user())


@patient_bp.get("/api/doctors")
@role_required("patient")
def doctors_api():
    q = request.args.get("q", "").strip()
    query = Doctor.query.filter_by(approved=True)
    if q:
        query = query.filter(Doctor.specialization.ilike(f"%{q}%"))
    return jsonify([doctor.to_card() for doctor in query.limit(40).all()])


@patient_bp.post("/api/appointments")
@role_required("patient")
def book_appointment():
    user = current_user()
    payload = request.get_json() or request.form
    try:
        scheduled_at = datetime.fromisoformat(payload.get("scheduled_at"))
        appointment = Appointment(
            patient_id=user.patient.id,
            doctor_id=int(payload.get("doctor_id")),
            scheduled_at=scheduled_at,
            mode=payload.get("mode", "video"),
            reason=payload.get("reason", "")[:255],
        )
        db.session.add(appointment)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"ok": False, "message": "That doctor is already booked for this time."}), 409
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "Invalid appointment details."}), 400

    db.session.add(Notification(user_id=appointment.doctor.user_id, title="New appointment", body=f"{user.name} requested a consultation.", category="appointment"))
    db.session.commit()
    return jsonify({"ok": True, "appointment": appointment.to_dict()}), 201


@patient_bp.get("/api/appointments")
@role_required("patient")
def patient_appointments_api():
    user = current_user()
    appointments = Appointment.query.filter_by(patient_id=user.patient.id).order_by(Appointment.scheduled_at.desc()).all()
    return jsonify([appointment.to_dict() for appointment in appointments])


@patient_bp.post("/api/reports")
@role_required("patient")
def upload_report():
    user = current_user()
    uploaded = request.files.get("report")
    title = request.form.get("title", "Medical report").strip()
    if not uploaded or not allowed_file(uploaded.filename):
        return jsonify({"ok": False, "message": "Upload a valid PDF, image, or document."}), 400
    filename = secure_filename(f"patient_{user.patient.id}_{int(datetime.utcnow().timestamp())}_{uploaded.filename}")
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    uploaded.save(path)
    db.session.add(MedicalReport(patient_id=user.patient.id, title=title, file_path=filename))
    db.session.commit()
    return jsonify({"ok": True, "filename": filename})


@patient_bp.get("/prescriptions/<int:prescription_id>/download")
@role_required("patient", "doctor")
def download_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], prescription.file_path, as_attachment=True)


@patient_bp.get("/api/messages/<int:appointment_id>")
@role_required("patient", "doctor")
def chat_history(appointment_id):
    messages = Message.query.filter_by(appointment_id=appointment_id).order_by(Message.created_at.asc()).all()
    return jsonify([message.to_dict() for message in messages])
