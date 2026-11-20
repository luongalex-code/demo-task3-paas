"""HTTPS-only administrator sign-in and account provisioning."""

import re
import secrets

import click
import pymysql
from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from pymysql.constants import ER
from werkzeug.security import check_password_hash, generate_password_hash

from db import PROJECT_ROOT, DatabaseUnavailable, db_cursor


auth = Blueprint("auth", __name__)
USERNAME = re.compile(r"[a-z0-9][a-z0-9_.-]{2,31}")
MIN_PASSWORD = 12
MAX_PASSWORD = 128
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_urlsafe(32), method="scrypt")


def session_configured():
    return len(current_app.secret_key or "") >= 32


def signed_in():
    return request.is_secure and session_configured() and session.get("admin_id") is not None


def csrf_token():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def valid_csrf():
    if request.headers.get("Sec-Fetch-Site") in {"cross-site", "same-site"}:
        return False
    expected = session.get("csrf_token")
    submitted = request.form.get("csrf_token", "")
    return bool(expected and secrets.compare_digest(expected.encode(), submitted.encode()))


@auth.app_context_processor
def form_context():
    return {"signed_in": signed_in(), "csrf_token": csrf_token}


@auth.after_request
def protect_auth_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@auth.errorhandler(DatabaseUnavailable)
def auth_database_unavailable(_error):
    return render_template("login.html", blocked=True, error="Tạm thời không thể đăng nhập. Vui lòng thử lại sau."), 503


@auth.route("/login", methods=["GET", "POST"])
def login():
    if not request.is_secure:
        return render_template("login.html", blocked=True, error="Đăng nhập yêu cầu truy cập qua HTTPS."), 403
    if not session_configured():
        return render_template("login.html", blocked=True, error="Đăng nhập chưa được kích hoạt."), 503

    if request.method == "POST":
        if not valid_csrf():
            return render_template("login.html", error="Biểu mẫu không hợp lệ. Vui lòng thử lại."), 403

        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        account = None
        if USERNAME.fullmatch(username) and MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
            with db_cursor() as cursor:
                cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
                account = cursor.fetchone()
            stored_hash = account["password_hash"] if account else DUMMY_PASSWORD_HASH
            if check_password_hash(stored_hash, password) and account:
                session.clear()
                session.permanent = True
                session["admin_id"] = account["id"]
                return redirect(url_for("notes.index"), code=303)

        return render_template("login.html", error="Tên đăng nhập hoặc mật khẩu không đúng."), 401

    if signed_in():
        return redirect(url_for("notes.index"))
    return render_template("login.html")


@auth.post("/logout")
def logout():
    if not signed_in() or not valid_csrf():
        return render_template("login.html", blocked=True, error="Yêu cầu đăng xuất không hợp lệ."), 403
    session.clear()
    return redirect(url_for("notes.index"), code=303)


@auth.cli.command("create-admin")
@click.argument("username")
def create_admin(username):
    """Initialize the users table and provision an administrator."""
    username = username.strip().lower()
    if not USERNAME.fullmatch(username):
        raise click.ClickException("Tên đăng nhập cần 3–32 ký tự ASCII: a–z, 0–9, dấu chấm, gạch dưới hoặc gạch ngang.")

    password = click.prompt("Mật khẩu quản trị (12–128 ký tự)", hide_input=True, confirmation_prompt=True)
    if not MIN_PASSWORD <= len(password) <= MAX_PASSWORD or not password.strip():
        raise click.ClickException("Mật khẩu phải có 12–128 ký tự và chứa ký tự khác khoảng trắng.")

    password_hash = generate_password_hash(password, method="scrypt")
    try:
        with db_cursor() as cursor:
            cursor.execute((PROJECT_ROOT / "sql" / "users.sql").read_text(encoding="utf-8"))
            try:
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
            except pymysql.err.IntegrityError as error:
                if error.args[0] == ER.DUP_ENTRY:
                    raise click.ClickException("Tên đăng nhập đã tồn tại.") from None
                raise
    except DatabaseUnavailable:
        raise click.ClickException("Không thể tạo tài khoản. Kiểm tra kết nối MySQL, TLS và quyền tạo bảng hoặc thêm bản ghi.") from None

    click.echo("Đã tạo tài khoản quản trị.")
