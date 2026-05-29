from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from models import db
from models.user_model import Doctor, Patient, User
from routes import redirect_for_role


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    if session.get("user_id"):
        user = User.query.get(session["user_id"])
        if user:
            return redirect_for_role(user)
    return render_template("index.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "patient")
        phone = request.form.get("phone", "").strip()

        if role not in {"patient", "doctor"}:
            flash("Only patients and doctors can self-register.", "danger")
            return redirect(url_for("auth.register"))
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("auth.register"))
        if not name or "@" not in email:
            flash("Please enter a valid name and email.", "danger")
            return redirect(url_for("auth.register"))

        user = User(name=name, email=email, role=role, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role == "doctor":
            db.session.add(
                Doctor(
                    user_id=user.id,
                    specialization=request.form.get("specialization", "General Medicine"),
                    qualification=request.form.get("qualification", ""),
                    experience_years=int(request.form.get("experience_years") or 0),
                    consultation_fee=request.form.get("consultation_fee") or 0,
                    approved=False,
                )
            )
        else:
            db.session.add(Patient(user_id=user.id, gender=request.form.get("gender"), blood_group=request.form.get("blood_group")))

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account already exists for this email.", "danger")
            return redirect(url_for("auth.register"))

        flash("Registration successful. Doctors require admin approval before appointments.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password) or not user.is_active:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        session.clear()
        session.permanent = True
        session["user_id"] = user.id
        session["role"] = user.role
        flash(f"Welcome back, {user.name}.", "success")
        return redirect_for_role(user)

    return render_template("login.html")


@auth_bp.route("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")


@auth_bp.route("/contact")
def contact():
    return render_template("contact.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
