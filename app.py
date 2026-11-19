"""Demo Flask cho bài thực hành triển khai PaaS trên Render."""

import os
import socket
import time

from flask import Flask, jsonify, render_template

app = Flask(__name__)
app.json.ensure_ascii = False


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
