"""Demo Flask cho bài thực hành triển khai PaaS trên Render."""

import os

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
    )


if __name__ == "__main__":
    # Windows: python app.py. Render imports app via gunicorn app:app.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
