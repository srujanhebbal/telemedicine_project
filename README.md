#terminal kill cmds
lsof -i :5002

COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME Python 1929 srujanhebbal 3u IPv4 0xc758fef3afd61718 0t0 TCP *:rfe (LISTEN) Python 1938 srujanhebbal 3u IPv4 0xc758fef3afd61718 0t0 TCP *:rfe (LISTEN) Python 1938 srujanhebbal 5u IPv4 0xc758fef3afd61718 0t0 TCP *:rfe (LISTEN)

kill -9 1929 1938

# MediConnect Telemedicine Web Application

MediConnect is a full-stack Flask, MySQL, Socket.IO, and WebRTC telemedicine portal with role-based dashboards for patients, doctors, and admins. It includes secure registration/login, appointment booking with double-booking protection, real-time chat, WebRTC consultation rooms, uploads, prescriptions, notifications, reminders, and a responsive healthcare glassmorphism UI.

## Tech Stack

- Frontend: HTML5, CSS3, JavaScript ES6, Fetch API
- Backend: Python Flask, Blueprints, Flask-SQLAlchemy
- Database: MySQL with PyMySQL
- Realtime: Flask-SocketIO and WebRTC signaling
- Security: password hashing, sessions, role guards, CSRF on auth forms, SQLAlchemy query binding, secure file names

## Project Structure

```text
app.py
config.py
requirements.txt
static/css/style.css
static/js/main.js
static/js/webrtc.js
templates/
routes/
models/
uploads/
database/schema.sql
```

## MySQL Setup

```sql
CREATE USER IF NOT EXISTS 'telemed_user'@'localhost' IDENTIFIED BY 'telemed_password';
GRANT ALL PRIVILEGES ON telemedicine_db.* TO 'telemed_user'@'localhost';
FLUSH PRIVILEGES;
```

Then run the schema:

```bash
mysql -u root -p < database/schema.sql
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your real `SECRET_KEY` and `DATABASE_URL`.

## Initialize and Seed

```bash
export FLASK_APP=app.py
flask init-db
flask seed-demo
```

Demo accounts:

- Admin: `admin@telemed.local` / `Admin@12345`
- Doctor: `dr.lee@telemed.local` / `Doctor@12345`
- Patient: `patient@telemed.local` / `Patient@12345`

## Run

```bash
flask run --host=0.0.0.0 --port=5000
```

Open `http://localhost:5000`.

## VS Code Setup

1. Open this folder in VS Code.
2. Create and activate `.venv`.
3. Install requirements.
4. Copy `.env.example` to `.env`.
5. Select `.venv/bin/python` as the interpreter.
6. Use the included `Flask: MediConnect` launch configuration.

## Production Notes

- Replace the default `SECRET_KEY`.
- Use HTTPS so camera, microphone, and secure cookies work reliably in production.
- Set `APP_CONFIG=config.ProductionConfig`.
- Use a production Socket.IO server setup such as eventlet/gevent behind Nginx.
- Store uploads in private object storage for real deployments.
- Add email delivery for forgot-password tokens before enabling reset links.
- Add audit logging and full clinical compliance controls for regulated use.
