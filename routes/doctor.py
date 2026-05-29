import os
from datetime import datetime
from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename
from models import db
from models.appointment_model import Appointment, Notification, Prescription
from routes import current_user, role_required


doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")


@doctor_bp.route("/dashboard")
@role_required("doctor")
def dashboard():
    user = current_user()
    appointments = Appointment.query.filter_by(doctor_id=user.doctor.id).order_by(Appointment.scheduled_at.desc()).limit(10).all()
    return render_template("doctor_dashboard.html", user=user, appointments=appointments)


@doctor_bp.route("/chat/<int:appointment_id>")
@role_required("doctor")
def chat_page(appointment_id):
    return render_template("chat.html", user=current_user(), appointment_id=appointment_id)


@doctor_bp.route("/consultation/<int:appointment_id>")
@role_required("doctor")
def consultation_page(appointment_id):
    return render_template("video_consultation.html", user=current_user(), appointment_id=appointment_id)


@doctor_bp.post("/api/appointments/<int:appointment_id>/status")
@role_required("doctor")
def update_appointment_status(appointment_id):
    user = current_user()
    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=user.doctor.id).first_or_404()
    status = (request.get_json() or {}).get("status")
    if status not in {"Approved", "Rejected", "Completed"}:
        return jsonify({"ok": False, "message": "Invalid status."}), 400
    appointment.status = status
    db.session.add(Notification(user_id=appointment.patient.user_id, title="Appointment updated", body=f"Your appointment is {status.lower()}.", category="appointment"))
    db.session.commit()
    return jsonify({"ok": True, "appointment": appointment.to_dict()})


@doctor_bp.post("/api/profile")
@role_required("doctor")
def update_profile():
    user = current_user()
    payload = request.get_json() or {}
    doctor = user.doctor
    doctor.specialization = payload.get("specialization", doctor.specialization)
    doctor.qualification = payload.get("qualification", doctor.qualification)
    doctor.experience_years = int(payload.get("experience_years", doctor.experience_years) or 0)
    doctor.consultation_fee = payload.get("consultation_fee", doctor.consultation_fee)
    doctor.bio = payload.get("bio", doctor.bio)
    doctor.availability = payload.get("availability", doctor.availability)
    db.session.commit()
    return jsonify({"ok": True, "doctor": doctor.to_card()})


@doctor_bp.post("/api/prescriptions")
@role_required("doctor")
def upload_prescription():
    user = current_user()
    appointment = Appointment.query.filter_by(id=request.form.get("appointment_id"), doctor_id=user.doctor.id).first_or_404()
    uploaded = request.files.get("prescription")
    notes = request.form.get("notes", "")
    if uploaded:
        filename = secure_filename(f"rx_{appointment.id}_{int(datetime.utcnow().timestamp())}_{uploaded.filename}")
        uploaded.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    else:
        filename = None
    prescription = Prescription(
        appointment_id=appointment.id,
        doctor_id=user.doctor.id,
        patient_id=appointment.patient_id,
        notes=notes,
        file_path=filename,
    )
    db.session.add(prescription)
    db.session.add(Notification(user_id=appointment.patient.user_id, title="Prescription ready", body="Your prescription is available for download.", category="prescription"))
    db.session.commit()
    return jsonify({"ok": True, "prescription_id": prescription.id})
