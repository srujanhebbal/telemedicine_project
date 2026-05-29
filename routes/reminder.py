from datetime import datetime
from flask import Blueprint, jsonify, request
from models import db
from models.reminder_model import MedicineReminder
from routes import current_user, role_required


reminder_bp = Blueprint("reminder", __name__, url_prefix="/api/reminders")


@reminder_bp.get("")
@role_required("patient")
def list_reminders():
    user = current_user()
    reminders = MedicineReminder.query.filter_by(patient_id=user.patient.id).order_by(MedicineReminder.reminder_time.asc()).all()
    return jsonify([reminder.to_dict() for reminder in reminders])


@reminder_bp.post("")
@role_required("patient")
def create_reminder():
    user = current_user()
    payload = request.get_json() or {}
    try:
        reminder_time = datetime.strptime(payload.get("reminder_time"), "%H:%M").time()
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "Reminder time must be HH:MM."}), 400

    reminder = MedicineReminder(
        patient_id=user.patient.id,
        medicine_name=payload.get("medicine_name", "").strip(),
        dosage=payload.get("dosage", "").strip(),
        reminder_time=reminder_time,
        schedule=payload.get("schedule", "Daily"),
    )
    if not reminder.medicine_name or not reminder.dosage:
        return jsonify({"ok": False, "message": "Medicine name and dosage are required."}), 400
    db.session.add(reminder)
    db.session.commit()
    return jsonify({"ok": True, "reminder": reminder.to_dict()}), 201


@reminder_bp.patch("/<int:reminder_id>")
@role_required("patient")
def update_reminder(reminder_id):
    user = current_user()
    reminder = MedicineReminder.query.filter_by(id=reminder_id, patient_id=user.patient.id).first_or_404()
    payload = request.get_json() or {}
    action = payload.get("action")
    if action == "taken":
        reminder.taken_count += 1
    elif action == "missed":
        reminder.missed_count += 1
    elif "is_active" in payload:
        reminder.is_active = bool(payload["is_active"])
    db.session.commit()
    return jsonify({"ok": True, "reminder": reminder.to_dict()})
