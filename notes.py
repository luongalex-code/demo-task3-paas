"""Routes and form validation for study notes."""

from flask import Blueprint, redirect, render_template, request, url_for

from auth import signed_in, valid_csrf
from db import DatabaseUnavailable, db_cursor


notes = Blueprint("notes", __name__, url_prefix="/notes")
MAX_CONTENT = 255
MAX_NOTE_ID = 2_147_483_647
RESULT_MESSAGES = {
    "created": "Đã thêm ghi chú.",
    "updated": "Đã lưu thay đổi.",
    "deleted": "Đã xóa ghi chú.",
}


@notes.before_request
def protect_note_actions():
    if request.endpoint == "notes.index" and request.method in {"GET", "HEAD"}:
        return

    if not signed_in():
        if request.method in {"GET", "HEAD"}:
            return redirect(url_for("auth.login"))
        return render_template("notes.html", page_error="Hãy đăng nhập qua HTTPS để thay đổi ghi chú."), 403

    if request.method == "POST" and not valid_csrf():
        return render_template("notes.html", page_error="Biểu mẫu đã hết hiệu lực. Hãy mở lại trang ghi chú và thử lại."), 403


@notes.after_request
def protect_forms(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@notes.errorhandler(DatabaseUnavailable)
def database_unavailable(_error):
    return render_template("notes.html", page_error="Tạm thời không thể truy cập ghi chú. Vui lòng thử lại sau."), 503


def render_form(*, status=200, **context):
    return render_template("notes.html", max_content=MAX_CONTENT, **context), status


def submitted_content():
    content = request.form.get("content", "").strip()
    if not content or len(content) > MAX_CONTENT:
        return content, f"Nhập nội dung từ 1 đến {MAX_CONTENT} ký tự."
    return content, None


def show_list(content="", form_error=None):
    with db_cursor(for_notes=True) as cursor:
        cursor.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC")
        records = cursor.fetchall()
    return render_form(
        records=records,
        content=content,
        form_error=form_error,
        result=RESULT_MESSAGES.get(request.args.get("result")) if not form_error else None,
        status=422 if form_error else 200,
    )


def find_note(note_id):
    with db_cursor(for_notes=True) as cursor:
        cursor.execute("SELECT id, content FROM notes WHERE id = %s", (note_id,))
        return cursor.fetchone()


def note_missing():
    return render_template("notes.html", page_error="Không tìm thấy ghi chú. Có thể ghi chú đã được xóa."), 404


@notes.route("", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        content, form_error = submitted_content()
        if form_error:
            return show_list(content, form_error)
        with db_cursor(for_notes=True) as cursor:
            cursor.execute("INSERT INTO notes (content) VALUES (%s)", (content,))
        return redirect(url_for("notes.index", result="created"), code=303)
    return show_list()


@notes.route("/<int:note_id>/edit", methods=["GET", "POST"])
def edit(note_id):
    if not 1 <= note_id <= MAX_NOTE_ID:
        return note_missing()
    if request.method == "POST":
        content, form_error = submitted_content()
        if form_error:
            if not find_note(note_id):
                return note_missing()
            return render_form(mode="edit", note_id=note_id, content=content, form_error=form_error, status=422)
        with db_cursor(for_notes=True) as cursor:
            cursor.execute("UPDATE notes SET content = %s WHERE id = %s", (content, note_id))
            if not cursor.rowcount:
                return note_missing()
        return redirect(url_for("notes.index", result="updated"), code=303)

    record = find_note(note_id)
    if not record:
        return note_missing()
    return render_form(mode="edit", note_id=note_id, content=record["content"])


@notes.route("/<int:note_id>/delete", methods=["GET", "POST"])
def delete(note_id):
    if not 1 <= note_id <= MAX_NOTE_ID:
        return note_missing()
    if request.method == "POST":
        with db_cursor(for_notes=True) as cursor:
            cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
            if not cursor.rowcount:
                return note_missing()
        return redirect(url_for("notes.index", result="deleted"), code=303)

    record = find_note(note_id)
    if not record:
        return note_missing()
    return render_form(mode="delete", note_id=note_id, content=record["content"])
