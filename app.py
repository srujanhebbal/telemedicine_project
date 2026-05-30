import os
from flask import Flask, jsonify, render_template, session
from flask_socketio import SocketIO, emit, join_room
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from models import db
from models.appointment_model import Appointment, Message, Notification
from models.user_model import Doctor, Patient, User
from routes.auth import auth_bp
from routes.patient import patient_bp
from routes.doctor import doctor_bp
from routes.admin import admin_bp
from routes.reminder import reminder_bp


socketio = SocketIO(cors_allowed_origins=[], async_mode="threading")
csrf = CSRFProtect()


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(os.environ.get("APP_CONFIG", "config.DevelopmentConfig"))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, manage_session=False)

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reminder_bp)

    csrf.exempt(patient_bp)
    csrf.exempt(doctor_bp)
    csrf.exempt(admin_bp)
    csrf.exempt(reminder_bp)

    @app.context_processor
    def inject_globals():
        user = User.query.get(session["user_id"]) if session.get("user_id") else None
        unread = (
            Notification.query.filter_by(user_id=user.id, is_read=False).count()
            if user
            else 0
        )
        return {
            "current_user": user,
            "unread_notifications": unread,
        }

    @app.errorhandler(403)
    def forbidden(_error):
        return (
            render_template(
                "error.html",
                code=403,
                message="You do not have permission to view this page.",
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(_error):
        return (
            render_template(
                "error.html",
                code=404,
                message="The page you requested was not found.",
            ),
            404,
        )

    @app.get("/api/notifications")
    def notifications_api():
        if not session.get("user_id"):
            return jsonify([])

        notifications = (
            Notification.query.filter_by(user_id=session["user_id"])
            .order_by(Notification.created_at.desc())
            .limit(30)
            .all()
        )

        return jsonify([item.to_dict() for item in notifications])

    @app.cli.command("init-db")
    def init_db():
        db.create_all()

        if not User.query.filter_by(email="admin@telemed.local").first():
            admin = User(
                name="System Admin",
                email="admin@telemed.local",
                role="admin",
                phone="+10000000000",
            )
            admin.set_password("Admin@12345")
            db.session.add(admin)
            db.session.commit()

        print("Database initialized.")
        print("Admin login: admin@telemed.local / Admin@12345")

    @app.cli.command("seed-demo")
    def seed_demo():
        db.create_all()

        demo_doctors = [
            {
                "name": "Dr. Amelia Lee",
                "email": "dr.lee@telemed.local",
                "phone": "+15550101",
                "specialization": "Cardiology",
                "qualification": "MD, FACC",
                "experience_years": 11,
                "consultation_fee": 75,
                "bio": "Heart care specialist focused on preventive cardiology.",
            },
            {
                "name": "Dr. Noah Patel",
                "email": "dr.patel@telemed.local",
                "phone": "+15550102",
                "specialization": "Dermatology",
                "qualification": "MBBS, MD Dermatology",
                "experience_years": 8,
                "consultation_fee": 60,
                "bio": "Skin, hair, allergy, and acne care consultant.",
            },
            {
                "name": "Dr. Sofia Chen",
                "email": "dr.chen@telemed.local",
                "phone": "+15550103",
                "specialization": "Pediatrics",
                "qualification": "MBBS, DCH",
                "experience_years": 9,
                "consultation_fee": 55,
                "bio": "Child health specialist for routine and urgent pediatric care.",
            },
            {
                "name": "Dr. Arjun Rao",
                "email": "dr.rao@telemed.local",
                "phone": "+15550104",
                "specialization": "General Medicine",
                "qualification": "MBBS, MD Internal Medicine",
                "experience_years": 13,
                "consultation_fee": 50,
                "bio": "Primary care physician for fever, diabetes, hypertension, and follow-ups.",
            },
        ]

        for item in demo_doctors:
            if not User.query.filter_by(email=item["email"]).first():
                doctor_user = User(
                    name=item["name"],
                    email=item["email"],
                    role="doctor",
                    phone=item["phone"],
                )
                doctor_user.set_password("Doctor@12345")
                db.session.add(doctor_user)
                db.session.flush()

                db.session.add(
                    Doctor(
                        user_id=doctor_user.id,
                        specialization=item["specialization"],
                        qualification=item["qualification"],
                        experience_years=item["experience_years"],
                        consultation_fee=item["consultation_fee"],
                        approved=True,
                        bio=item["bio"],
                    )
                )

        if not User.query.filter_by(email="patient@telemed.local").first():
            patient_user = User(
                name="Jordan Patient",
                email="patient@telemed.local",
                role="patient",
                phone="+15550202",
            )
            patient_user.set_password("Patient@12345")
            db.session.add(patient_user)
            db.session.flush()

            db.session.add(
                Patient(
                    user_id=patient_user.id,
                    gender="Other",
                    blood_group="O+",
                )
            )

        db.session.commit()

        print("Demo data seeded.")
        print("Doctor password for all demo doctors: Doctor@12345")
        print("Patient login: patient@telemed.local / Patient@12345")

    return app


@socketio.on("join")
def handle_join(data):
    appointment_id = data.get("appointment_id")

    if not session.get("user_id") or not appointment_id:
        return

    join_room(f"appointment:{appointment_id}")

    emit(
        "system",
        {"message": "Connected to consultation room."},
        room=f"appointment:{appointment_id}",
    )


@socketio.on("chat_message")
def handle_chat(data):
    if not session.get("user_id"):
        return

    appointment = Appointment.query.get(data.get("appointment_id"))

    if not appointment:
        return

    sender_id = session["user_id"]

    if sender_id == appointment.patient.user_id:
        receiver_id = appointment.doctor.user_id
    else:
        receiver_id = appointment.patient.user_id

    message = Message(
        appointment_id=appointment.id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        body=(data.get("body") or "")[:1500],
    )

    db.session.add(message)

    db.session.add(
        Notification(
            user_id=receiver_id,
            title="New message",
            body="You received a consultation message.",
            category="message",
        )
    )

    db.session.commit()

    emit(
        "chat_message",
        message.to_dict(),
        room=f"appointment:{appointment.id}",
    )


@socketio.on("webrtc_signal")
def handle_webrtc_signal(data):
    if not session.get("user_id"):
        return

    appointment_id = data.get("appointment_id")

    emit(
        "webrtc_signal",
        data,
        room=f"appointment:{appointment_id}",
        include_self=False,
    )


if __name__ == "__main__":
    socketio.run(
        create_app(),
        host="0.0.0.0",
        port=5002,
        debug=True,
    )