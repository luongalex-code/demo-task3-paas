"""Website Profile sinh viên và ứng dụng ghi chú học tập."""

import os
import socket
import time
from datetime import timedelta

from flask import Flask, jsonify, render_template

from auth import auth
from notes import notes

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or None,
    SESSION_COOKIE_NAME="__Host-student_profile",
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_COOKIE_PATH="/",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SESSION_REFRESH_EACH_REQUEST=False,
)
app.json.ensure_ascii = False
app.register_blueprint(auth)
app.register_blueprint(notes)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(
        status="ok",
        message="Python Flask application is running successfully",
        host=socket.gethostname(),
    )


@app.get("/stress")
def stress():
    # Tạo tải CPU trong khoảng hai giây để kiểm thử Auto Scaling.
    end_time = time.monotonic() + 2.0
    total = 0
    while time.monotonic() < end_time:
        total += 12345 * 67890
    return jsonify(status="stressed", host=socket.gethostname())


if __name__ == "__main__":
    # Windows: python app.py. Render imports app via gunicorn app:app.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
