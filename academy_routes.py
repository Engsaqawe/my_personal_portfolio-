"""Public ENGSAQAWE Academy and its administrator and student learning panels."""

import re
import os
import uuid
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.parse import urlparse, parse_qs
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, current_app, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from auth import admin_required, get_admin_by_id
from db_helpers import query_all, query_one, execute, execute_returning_id
from site_settings import get_site_settings

academy_bp = Blueprint("academy", __name__, url_prefix="/academy")
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov", ".m4v"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@academy_bp.app_context_processor
def inject_academy_cart_count():
    student_id = session.get("academy_student_id")
    count = query_one(
        """SELECT COUNT(*) AS c FROM academy_cart_items ci JOIN courses c ON c.id=ci.course_id
           WHERE ci.student_id=%s AND c.status='published'""",
        (student_id,),
    )["c"] if student_id else 0
    return {"academy_cart_count": count}


def student_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        student_id = session.get("academy_student_id")
        student = query_one(
            "SELECT id,name FROM academy_students WHERE id=%s AND status='active'",
            (student_id,),
        ) if student_id else None
        if not student:
            session.pop("academy_student_id", None)
            session.pop("academy_student_name", None)
            flash("Sign in to continue your course.", "error")
            return redirect(url_for("academy.login", next=request.path))
        session["academy_student_name"] = student["name"]
        return view(*args, **kwargs)
    return wrapped


def safe_return_path(value):
    return value if value.startswith("/academy/") and not value.startswith("//") and "\\" not in value else ""


def video_player_url(value):
    """Return a safe provider embed URL for supported platforms, or None for direct video."""
    try:
        parsed = urlparse(value or "")
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{6,32}", video_id):
            return f"https://www.youtube.com/embed/{video_id}?playsinline=1&rel=0"
        return None
    if host == "youtube-nocookie.com" or host.endswith(".youtube-nocookie.com"):
        if parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/", 2)[2].split("/", 1)[0]
            if re.fullmatch(r"[A-Za-z0-9_-]{6,32}", video_id):
                return f"https://www.youtube.com/embed/{video_id}?playsinline=1&rel=0"
        return None
    if host == "youtube.com" or host.endswith(".youtube.com"):
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        if not video_id:
            match = re.match(r"^/(?:embed|shorts|live|v)/([A-Za-z0-9_-]{6,32})(?:/|$)", parsed.path)
            video_id = match.group(1) if match else ""
        if re.fullmatch(r"[A-Za-z0-9_-]{6,32}", video_id):
            return f"https://www.youtube.com/embed/{video_id}?playsinline=1&rel=0"
        playlist_id = parse_qs(parsed.query).get("list", [""])[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{10,100}", playlist_id):
            return f"https://www.youtube.com/embed/videoseries?list={playlist_id}"
        return None
    if host in {"vimeo.com", "www.vimeo.com", "player.vimeo.com"}:
        match = re.search(r"/(?:video/)?(\d+)", parsed.path)
        return f"https://player.vimeo.com/video/{match.group(1)}" if match else None
    return None


def is_youtube_url(value):
    try:
        host = (urlparse(value or "").hostname or "").lower()
    except ValueError:
        return False
    return host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com") or host == "youtube-nocookie.com" or host.endswith(".youtube-nocookie.com")


def valid_video_url(value):
    value = (value or "").strip()
    if not value or len(value) > 1000 or "\\" in value or any(ord(char) < 32 for char in value):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    if value.startswith("/academy/media/"):
        return bool(re.fullmatch(r"/academy/media/[a-f0-9-]{36}\.(?:mp4|webm|ogg|mov|m4v)", value))
    return parsed.scheme == "https" and bool(parsed.netloc)


def save_academy_upload(file_storage, kind):
    """Save a checked upload under a generated name and return its static URL."""
    if not file_storage or not file_storage.filename:
        return None
    original = secure_filename(file_storage.filename)
    extension = os.path.splitext(original)[1].lower()
    allowed = VIDEO_EXTENSIONS if kind == "lessons" else IMAGE_EXTENSIONS
    if extension not in allowed:
        raise ValueError("Choose a supported video or image file.")
    if kind == "lessons":
        absolute_dir = os.path.join(current_app.instance_path, "academy_videos")
        url_dir = "/academy/media"
    else:
        relative_dir = os.path.join("uploads", "academy", kind)
        absolute_dir = os.path.join(current_app.static_folder, relative_dir)
        url_dir = f"/static/{relative_dir.replace(os.sep, '/')}"
    os.makedirs(absolute_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}{extension}"
    file_storage.save(os.path.join(absolute_dir, filename))
    return f"{url_dir}/{filename}"


def delete_academy_upload(value, kind):
    prefix = "/academy/media/" if kind == "lessons" else f"/static/uploads/academy/{kind}/"
    if not value or not value.startswith(prefix):
        return
    filename = value[len(prefix):]
    allowed = VIDEO_EXTENSIONS if kind == "lessons" else IMAGE_EXTENSIONS
    if filename != os.path.basename(filename) or os.path.splitext(filename)[1].lower() not in allowed:
        return
    path = (os.path.join(current_app.instance_path, "academy_videos", filename) if kind == "lessons"
            else os.path.join(current_app.static_folder, "uploads", "academy", kind, filename))
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


@academy_bp.route("/login", methods=["GET", "POST"])
def login():
    nxt = safe_return_path(request.args.get("next") or request.form.get("next") or "")
    if session.get("academy_student_id"):
        return redirect(nxt or url_for("academy.learning"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        student = query_one("SELECT * FROM academy_students WHERE LOWER(email) = %s AND status = 'active'", (email,))
        if student and student.get("password_hash") and check_password_hash(student["password_hash"], password):
            session.clear()
            session["academy_student_id"] = student["id"]
            session["academy_student_name"] = student["name"]
            flash("Welcome back to your learning space.", "success")
            return redirect(nxt or url_for("academy.learning"))
        flash("We could not sign you in with those details.", "error")

    return render_template("academy/student_login.html", next=nxt)


@academy_bp.route("/register", methods=["GET", "POST"])
def register():
    course_id = request.args.get("course_id") or request.form.get("course_id") or ""
    course = None
    if course_id:
        try:
            course_id = int(course_id)
        except ValueError:
            course_id = ""
        if course_id:
            course = query_one(
                """SELECT c.id,c.title,c.price FROM courses c WHERE c.id=%s AND c.status='published'
                   AND EXISTS (SELECT 1 FROM academy_lessons l WHERE l.course_id=c.id)""",
                (course_id,),
            )
            if not course:
                course_id = ""
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        existing = query_one("SELECT id, password_hash, status FROM academy_students WHERE LOWER(email)=%s ORDER BY id LIMIT 1", (email,)) if email else None
        if not name or len(name) > 120 or "@" not in email or len(email) > 180 or len(password) < 10:
            flash("Enter your name, a valid email, and a password with at least 10 characters.", "error")
        elif existing and existing.get("status") != "active":
            flash("This student account is deactivated. Contact the Academy administrator.", "error")
        elif existing and existing.get("password_hash"):
            flash("An account already uses this email. Please sign in instead.", "error")
        else:
            password_hash = generate_password_hash(password)
            if existing:
                execute("UPDATE academy_students SET name=%s, password_hash=%s, status='active' WHERE id=%s", (name, password_hash, existing["id"]))
                student_id = existing["id"]
            else:
                student_id = execute_returning_id(
                    "INSERT INTO academy_students (name,email,password_hash,status) VALUES (%s,%s,%s,'active')",
                    (name, email, password_hash),
                )
            session.clear()
            session["academy_student_id"] = student_id
            session["academy_student_name"] = name
            if course_id:
                if course and Decimal(str(course.get("price") or 0)) <= 0:
                    _enroll(student_id, course_id)
                elif course:
                    execute("INSERT IGNORE INTO academy_cart_items (student_id,course_id) VALUES (%s,%s)", (student_id, course_id))
                    return redirect(url_for("academy.cart"))
            return redirect(url_for("academy.learning"))
    return render_template("academy/student_register.html", course=course)


@academy_bp.route("/logout", methods=["POST"])
def logout():
    was_admin = bool(session.get("admin_id"))
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("admin.login" if was_admin else "academy.index"))


@academy_bp.route("/panel")
@admin_required
def dashboard():
    stats = {
        "courses": query_one("SELECT COUNT(*) AS c FROM courses")["c"],
        "students": query_one("SELECT COUNT(*) AS c FROM academy_students")["c"],
        "active": query_one("SELECT COUNT(*) AS c FROM academy_enrollments WHERE status = 'active'")["c"],
        "lessons": query_one("SELECT COUNT(*) AS c FROM academy_lessons")["c"],
        "avg_progress": query_one("SELECT COALESCE(AVG(progress), 0) AS a FROM academy_enrollments")["a"],
        "payments": query_one("SELECT COUNT(*) AS c FROM academy_payments WHERE status='demo_paid'")["c"],
        "demo_revenue": query_one("SELECT COALESCE(SUM(amount), 0) AS total FROM academy_payments WHERE status='demo_paid'")["total"],
    }
    courses = query_all("SELECT c.*, (SELECT COUNT(*) FROM academy_lessons l WHERE l.course_id=c.id) AS lesson_count FROM courses c ORDER BY c.sort_order ASC, c.id ASC LIMIT 6")
    recent = query_all(
        """SELECT s.*, COUNT(e.id) AS enrollment_count
           FROM academy_students s LEFT JOIN academy_enrollments e ON e.student_id=s.id
           GROUP BY s.id ORDER BY s.id DESC LIMIT 5"""
    )
    admin = get_admin_by_id(session["admin_id"])
    return render_template(
        "academy/dashboard.html",
        stats=stats,
        courses=courses,
        recent=recent,
        admin=admin,
    )


@academy_bp.route("/")
def index():
    search = (request.args.get("q") or "").strip()[:100]
    category_id = request.args.get("category", type=int)
    categories = query_all("SELECT id,name,slug FROM academy_categories ORDER BY sort_order,name")
    clauses = ["c.status='published'"]
    params = []
    if search:
        clauses.append("(c.title LIKE %s OR c.description LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    if category_id:
        clauses.append("c.category_id=%s")
        params.append(category_id)
    courses = query_all(
        f"""SELECT c.*,
               (SELECT COUNT(*) FROM academy_lessons l WHERE l.course_id=c.id) AS lesson_count,
               (SELECT name FROM academy_categories ac WHERE ac.id=c.category_id) AS category_name,
               (SELECT COUNT(*) FROM academy_course_actions a WHERE a.course_id=c.id AND a.is_liked=1) AS like_count
            FROM courses c WHERE {' AND '.join(clauses)} ORDER BY c.sort_order ASC, c.id ASC""",
        tuple(params),
    )
    settings = get_site_settings()
    return render_template("academy/public_index.html", courses=courses, settings=settings,
                           categories=categories, search=search, selected_category=category_id)


@academy_bp.route("/panel/courses")
@admin_required
def courses_list():
    search = (request.args.get("q") or "").strip()[:100]
    status = request.args.get("status", "all")
    category_id = request.args.get("category", type=int)
    categories = query_all("SELECT id,name FROM academy_categories ORDER BY sort_order,name")
    clauses, params = [], []
    if search:
        clauses.append("(c.title LIKE %s OR c.description LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    if status in {"draft", "published"}:
        clauses.append("c.status=%s")
        params.append(status)
    else:
        status = "all"
    if category_id:
        clauses.append("c.category_id=%s")
        params.append(category_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    courses = query_all(
        f"""SELECT c.*, (SELECT COUNT(*) FROM academy_lessons l WHERE l.course_id=c.id) AS lesson_count,
                   (SELECT name FROM academy_categories ac WHERE ac.id=c.category_id) AS category_name
            FROM courses c {where} ORDER BY c.sort_order ASC, c.id ASC""",
        tuple(params),
    )
    return render_template("academy/courses_list.html", courses=courses, categories=categories,
                           search=search, status=status, selected_category=category_id)


@academy_bp.route("/panel/courses/new", methods=["GET", "POST"])
@academy_bp.route("/panel/courses/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def course_form(item_id=None):
    course = query_one("SELECT * FROM courses WHERE id = %s", (item_id,)) if item_id else None
    categories = query_all("SELECT id,name FROM academy_categories ORDER BY sort_order,name")

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        modules = (request.form.get("modules") or "").strip()
        icon = (request.form.get("icon") or "fa-code").strip()
        thumbnail_url = (request.form.get("thumbnail_url") or "").strip()
        thumbnail_upload = request.files.get("thumbnail_file")
        remove_thumbnail = request.form.get("remove_thumbnail") == "1"
        category_id = request.form.get("category_id", type=int)
        currency = (request.form.get("currency") or "USD").strip().upper()
        try:
            price = Decimal((request.form.get("price") or "0").strip())
        except (InvalidOperation, ValueError):
            price = Decimal("-1")
        if not price.is_finite():
            price = Decimal("-1")
        level = (request.form.get("level") or "Beginner").strip()
        language = (request.form.get("language") or "English").strip()
        status = "published" if request.form.get("status") == "published" else "draft"
        progress = course.get("progress", 0) if course else 0
        try:
            sort_order = int(request.form.get("sort_order") or 0)
        except ValueError:
            sort_order = 0
        sort_order = max(-999999, min(999999, sort_order))
        progress = max(0, min(100, progress))

        if (not title or len(title) > 160 or not description or len(modules) > 80 or len(icon) > 60
                or len(level) > 50 or len(language) > 50 or len(thumbnail_url) > 500
                or (thumbnail_url and not (thumbnail_url.startswith("https://") or thumbnail_url.startswith("/static/")))
                or price < 0 or price > Decimal("999999.99") or not re.fullmatch(r"[A-Z]{3}", currency)
                or (category_id and not query_one("SELECT id FROM academy_categories WHERE id=%s", (category_id,)))):
            flash("Check the course details, category, cover URL, price, and 3-letter currency.", "error")
            return render_template("academy/course_form.html", course=course, categories=categories)

        old_thumbnail = course.get("thumbnail_url") if course else None
        if thumbnail_upload and thumbnail_upload.filename:
            try:
                thumbnail_url = save_academy_upload(thumbnail_upload, "covers")
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("academy/course_form.html", course=course, categories=categories)
        elif remove_thumbnail:
            thumbnail_url = ""
        elif not thumbnail_url:
            thumbnail_url = old_thumbnail or ""

        if course:
            execute(
                """UPDATE courses SET title=%s, description=%s, modules=%s,
                   progress=%s, icon=%s, thumbnail_url=%s, level=%s, language=%s,
                   status=%s, category_id=%s, price=%s, currency=%s, sort_order=%s WHERE id=%s""",
                (title, description, modules, progress, icon, thumbnail_url or None, level, language,
                 status, category_id or None, str(price), currency, sort_order, item_id),
            )
            if old_thumbnail and old_thumbnail != thumbnail_url:
                delete_academy_upload(old_thumbnail, "covers")
        else:
            new_course_id = execute_returning_id(
                """INSERT INTO courses (title, description, modules, progress, icon, thumbnail_url, level, language, status, category_id, price, currency, sort_order)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (title, description, modules, progress, icon, thumbnail_url or None, level, language,
                 status, category_id or None, str(price), currency, sort_order),
            )
            flash("Course created. Add the first video lesson, then publish when it is ready.", "success")
            return redirect(url_for("academy.lesson_form", course_id=new_course_id))
        flash("Course updated.", "success")
        return redirect(url_for("academy.courses_list"))

    return render_template("academy/course_form.html", course=course, categories=categories)


@academy_bp.route("/panel/categories")
@admin_required
def categories_list():
    categories = query_all(
        """SELECT ac.*,(SELECT COUNT(*) FROM courses c WHERE c.category_id=ac.id) AS course_count
           FROM academy_categories ac ORDER BY ac.sort_order,ac.name"""
    )
    return render_template("academy/categories_list.html", categories=categories)


@academy_bp.route("/panel/categories/new", methods=["GET", "POST"])
@academy_bp.route("/panel/categories/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def category_form(item_id=None):
    category = query_one("SELECT * FROM academy_categories WHERE id=%s", (item_id,)) if item_id else None
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        try:
            sort_order = int(request.form.get("sort_order") or 0)
        except ValueError:
            sort_order = 0
        sort_order = max(-999999, min(999999, sort_order))
        slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")[:120] or f"category-{uuid.uuid4().hex[:8]}"
        duplicate = query_one("SELECT id FROM academy_categories WHERE slug=%s AND id<>%s", (slug, item_id or 0))
        if not name or len(name) > 100 or len(description) > 500 or duplicate:
            flash("Enter a category name that is not already in use.", "error")
            return render_template("academy/category_form.html", category=category)
        if category:
            execute("UPDATE academy_categories SET name=%s,slug=%s,description=%s,sort_order=%s WHERE id=%s",
                    (name, slug, description or None, sort_order, item_id))
            flash("Category updated.", "success")
        else:
            execute("INSERT INTO academy_categories (name,slug,description,sort_order) VALUES (%s,%s,%s,%s)",
                    (name, slug, description or None, sort_order))
            flash("Category created.", "success")
        return redirect(url_for("academy.categories_list"))
    return render_template("academy/category_form.html", category=category)


@academy_bp.route("/panel/categories/<int:item_id>/delete", methods=["POST"])
@admin_required
def category_delete(item_id):
    execute("UPDATE courses SET category_id=NULL WHERE category_id=%s", (item_id,))
    execute("DELETE FROM academy_categories WHERE id=%s", (item_id,))
    flash("Category removed. Its courses remain in the catalog.", "success")
    return redirect(url_for("academy.categories_list"))


@academy_bp.route("/panel/courses/<int:item_id>/delete", methods=["POST"])
@admin_required
def course_delete(item_id):
    course = query_one("SELECT thumbnail_url FROM courses WHERE id=%s", (item_id,))
    lessons = query_all("SELECT video_url FROM academy_lessons WHERE course_id=%s", (item_id,))
    for lesson_row in lessons:
        delete_academy_upload(lesson_row.get("video_url"), "lessons")
    if course:
        delete_academy_upload(course.get("thumbnail_url"), "covers")
    execute("DELETE p FROM academy_lesson_progress p JOIN academy_lessons l ON l.id=p.lesson_id WHERE l.course_id=%s", (item_id,))
    execute("DELETE FROM academy_lessons WHERE course_id = %s", (item_id,))
    execute("DELETE FROM academy_enrollments WHERE course_id = %s", (item_id,))
    execute("DELETE FROM academy_payments WHERE course_id = %s", (item_id,))
    execute("DELETE FROM academy_course_actions WHERE course_id = %s", (item_id,))
    execute("DELETE FROM academy_cart_items WHERE course_id = %s", (item_id,))
    execute("UPDATE academy_students SET course_id=NULL WHERE course_id=%s", (item_id,))
    execute("DELETE FROM courses WHERE id = %s", (item_id,))
    flash("Course deleted.", "success")
    return redirect(url_for("academy.courses_list"))


@academy_bp.route("/panel/students")
@admin_required
def students_list():
    search = (request.args.get("q") or "").strip()[:100]
    status = request.args.get("status", "all")
    clauses, params = [], []
    if search:
        clauses.append("(s.name LIKE %s OR s.email LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    if status in {"active", "paused"}:
        clauses.append("s.status=%s")
        params.append(status)
    else:
        status = "all"
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    students = query_all(
        f"""SELECT s.*, COUNT(DISTINCT e.id) AS enrollment_count,
                   COUNT(DISTINCT p.id) AS payment_count
            FROM academy_students s LEFT JOIN academy_enrollments e ON e.student_id=s.id
            LEFT JOIN academy_payments p ON p.student_id=s.id {where}
            GROUP BY s.id ORDER BY s.id DESC""",
        tuple(params),
    )
    return render_template("academy/students_list.html", students=students, search=search, status=status)


@academy_bp.route("/panel/students/<int:item_id>")
@admin_required
def student_detail(item_id):
    student = query_one("SELECT * FROM academy_students WHERE id=%s", (item_id,))
    if not student:
        abort(404)
    enrollments = query_all(
        """SELECT e.*,c.title AS course_title FROM academy_enrollments e
           JOIN courses c ON c.id=e.course_id WHERE e.student_id=%s ORDER BY e.enrolled_at DESC""",
        (item_id,),
    )
    payments = query_all(
        """SELECT p.*,c.title AS course_title FROM academy_payments p
           LEFT JOIN courses c ON c.id=p.course_id WHERE p.student_id=%s ORDER BY p.created_at DESC""",
        (item_id,),
    )
    return render_template("academy/student_detail.html", student=student, enrollments=enrollments, payments=payments)


@academy_bp.route("/panel/students/<int:item_id>/status", methods=["POST"])
@admin_required
def student_toggle_status(item_id):
    student = query_one("SELECT id,status FROM academy_students WHERE id=%s", (item_id,))
    if not student:
        abort(404)
    new_status = "paused" if student["status"] == "active" else "active"
    execute("UPDATE academy_students SET status=%s WHERE id=%s", (new_status, item_id))
    flash(f"Student account {new_status}.", "success")
    return redirect(safe_return_path(request.form.get("next") or "") or url_for("academy.students_list"))


@academy_bp.route("/panel/students/new", methods=["GET", "POST"])
@academy_bp.route("/panel/students/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def student_form(item_id=None):
    student = query_one("SELECT * FROM academy_students WHERE id = %s", (item_id,)) if item_id else None
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        status = (request.form.get("status") or "active").strip()
        notes = (request.form.get("notes") or "").strip()
        status = status if status in {"active", "paused"} else "active"
        password = request.form.get("password") or ""

        duplicate = query_one("SELECT id FROM academy_students WHERE LOWER(email)=%s AND id<>%s LIMIT 1", (email, item_id or 0)) if email else None
        if not name or not email or "@" not in email or len(email) > 180 or duplicate:
            flash("Enter a unique name and valid email address.", "error")
            return render_template("academy/student_form.html", student=student)

        if student:
            if password:
                if len(password) < 10:
                    flash("Passwords must have at least 10 characters.", "error")
                    return render_template("academy/student_form.html", student=student)
                execute("UPDATE academy_students SET name=%s,email=%s,status=%s,notes=%s,password_hash=%s WHERE id=%s", (name, email, status, notes, generate_password_hash(password), item_id))
            else:
                execute("UPDATE academy_students SET name=%s,email=%s,status=%s,notes=%s WHERE id=%s", (name, email, status, notes, item_id))
            flash("Student updated.", "success")
        else:
            if len(password) < 10:
                flash("Set a password with at least 10 characters for the student account.", "error")
                return render_template("academy/student_form.html", student=student)
            execute(
                """INSERT INTO academy_students (name,email,password_hash,status,notes)
                   VALUES (%s,%s,%s,%s,%s)""",
                (name, email, generate_password_hash(password), status, notes),
            )
            flash("Student account created.", "success")
        return redirect(url_for("academy.students_list"))

    return render_template("academy/student_form.html", student=student)


@academy_bp.route("/panel/students/<int:item_id>/delete", methods=["POST"])
@admin_required
def student_delete(item_id):
    execute("DELETE FROM academy_lesson_progress WHERE student_id = %s", (item_id,))
    execute("DELETE FROM academy_enrollments WHERE student_id = %s", (item_id,))
    execute("DELETE FROM academy_payments WHERE student_id = %s", (item_id,))
    execute("DELETE FROM academy_course_actions WHERE student_id = %s", (item_id,))
    execute("DELETE FROM academy_cart_items WHERE student_id = %s", (item_id,))
    execute("DELETE FROM academy_students WHERE id = %s", (item_id,))
    flash("Student removed.", "success")
    return redirect(url_for("academy.students_list"))


def _enroll(student_id, course_id):
    existing = query_one(
        "SELECT id FROM academy_enrollments WHERE student_id=%s AND course_id=%s",
        (student_id, course_id),
    )
    if existing:
        execute("UPDATE academy_enrollments SET status='active' WHERE id=%s", (existing["id"],))
    else:
        execute(
            "INSERT INTO academy_enrollments (student_id,course_id,status,progress) VALUES (%s,%s,'active',0)",
            (student_id, course_id),
        )


@academy_bp.route("/courses/<int:course_id>")
def course_detail(course_id):
    course = query_one(
        """SELECT c.*,(SELECT name FROM academy_categories ac WHERE ac.id=c.category_id) AS category_name
           FROM courses c WHERE c.id=%s AND c.status='published'""",
        (course_id,),
    )
    if not course:
        abort(404)
    lessons = query_all(
        "SELECT id,title,duration,is_preview,sort_order FROM academy_lessons WHERE course_id=%s ORDER BY sort_order,id",
        (course_id,),
    )
    enrollment = None
    if session.get("academy_student_id"):
        enrollment = query_one(
            "SELECT * FROM academy_enrollments WHERE course_id=%s AND student_id=%s",
            (course_id, session["academy_student_id"]),
        )
    actions = query_one(
        """SELECT COALESCE(a.is_saved,0) AS is_saved,COALESCE(a.is_liked,0) AS is_liked,
                  (SELECT COUNT(*) FROM academy_course_actions x WHERE x.course_id=%s AND x.is_liked=1) AS like_count,
                  EXISTS(SELECT 1 FROM academy_cart_items ci WHERE ci.course_id=%s AND ci.student_id=%s) AS in_cart
           FROM courses c LEFT JOIN academy_course_actions a ON a.course_id=c.id AND a.student_id=%s
           WHERE c.id=%s""",
        (course_id, course_id, session.get("academy_student_id") or 0,
         session.get("academy_student_id") or 0, course_id),
    ) or {"is_saved": 0, "is_liked": 0, "like_count": 0, "in_cart": 0}
    continue_lesson = None
    if enrollment and enrollment.get("status") in {"active", "completed"}:
        continue_lesson = query_one(
            """SELECT l.id FROM academy_lessons l
               LEFT JOIN academy_lesson_progress p ON p.lesson_id=l.id AND p.student_id=%s
               WHERE l.course_id=%s AND p.id IS NULL
               ORDER BY l.sort_order,l.id LIMIT 1""",
            (session["academy_student_id"], course_id),
        )
        if not continue_lesson:
            continue_lesson = query_one(
                "SELECT id FROM academy_lessons WHERE course_id=%s ORDER BY sort_order,id LIMIT 1",
                (course_id,),
            )
    return render_template(
        "academy/course_detail.html", course=course, lessons=lessons,
        enrollment=enrollment, continue_lesson_id=continue_lesson["id"] if continue_lesson else None,
        settings=get_site_settings(), actions=actions,
    )


@academy_bp.route("/courses/<int:course_id>/action/<action>", methods=["POST"])
@student_required
def course_action(course_id, action):
    if action not in {"save", "like", "cart"}:
        abort(404)
    course = query_one(
        """SELECT c.id FROM courses c WHERE c.id=%s AND c.status='published'
           AND EXISTS (SELECT 1 FROM academy_lessons l WHERE l.course_id=c.id)""",
        (course_id,),
    )
    if not course:
        abort(404)
    student_id = session["academy_student_id"]
    if action == "cart":
        enrolled = query_one(
            "SELECT id FROM academy_enrollments WHERE student_id=%s AND course_id=%s AND status IN ('active','completed')",
            (student_id, course_id),
        )
        if not enrolled:
            execute("INSERT IGNORE INTO academy_cart_items (student_id,course_id) VALUES (%s,%s)", (student_id, course_id))
            flash("Course added to your cart.", "success")
        else:
            flash("You already have access to this course.", "success")
    else:
        column = "is_saved" if action == "save" else "is_liked"
        execute(
            f"""INSERT INTO academy_course_actions (student_id,course_id,{column}) VALUES (%s,%s,1)
                ON DUPLICATE KEY UPDATE {column}=1-{column}""",
            (student_id, course_id),
        )
        flash("Course saved." if action == "save" else "Thanks for liking this course.", "success")
    destination = safe_return_path(request.form.get("next") or "")
    return redirect(destination or url_for("academy.course_detail", course_id=course_id))


@academy_bp.route("/cart")
@student_required
def cart():
    items = query_all(
        """SELECT c.*,ci.added_at,(SELECT COUNT(*) FROM academy_lessons l WHERE l.course_id=c.id) AS lesson_count,
                  (SELECT name FROM academy_categories ac WHERE ac.id=c.category_id) AS category_name
           FROM academy_cart_items ci JOIN courses c ON c.id=ci.course_id
           WHERE ci.student_id=%s AND c.status='published' ORDER BY ci.added_at DESC""",
        (session["academy_student_id"],),
    )
    totals = {}
    for item in items:
        code = item.get("currency") or "USD"
        totals[code] = totals.get(code, 0) + float(item.get("price") or 0)
    return render_template("academy/cart.html", items=items, totals=totals)


@academy_bp.route("/cart/remove/<int:course_id>", methods=["POST"])
@student_required
def cart_remove(course_id):
    execute("DELETE FROM academy_cart_items WHERE student_id=%s AND course_id=%s",
            (session["academy_student_id"], course_id))
    flash("Course removed from your cart.", "success")
    return redirect(url_for("academy.cart"))


@academy_bp.route("/cart/checkout", methods=["GET", "POST"])
@student_required
def cart_checkout():
    student_id = session["academy_student_id"]
    items = query_all(
        """SELECT c.*,(SELECT COUNT(*) FROM academy_lessons l WHERE l.course_id=c.id) AS lesson_count
           FROM academy_cart_items ci JOIN courses c ON c.id=ci.course_id
           WHERE ci.student_id=%s AND c.status='published'
           AND EXISTS (SELECT 1 FROM academy_lessons l WHERE l.course_id=c.id)""",
        (student_id,),
    )
    if not items:
        flash("Your cart has no available courses.", "error")
        return redirect(url_for("academy.cart"))
    if request.method == "GET":
        totals = {}
        for item in items:
            code = item.get("currency") or "USD"
            totals[code] = totals.get(code, Decimal("0.00")) + Decimal(str(item.get("price") or 0))
        student = query_one("SELECT name,email FROM academy_students WHERE id=%s", (student_id,))
        return render_template("academy/cart_checkout.html", items=items, totals=totals, student=student)
    for item in items:
        if Decimal(str(item["price"] or 0)) > 0:
            existing = query_one(
                "SELECT id FROM academy_payments WHERE student_id=%s AND course_id=%s AND status='demo_paid' LIMIT 1",
                (student_id, item["id"]),
            )
            if not existing:
                execute(
                    """INSERT INTO academy_payments (student_id,course_id,amount,currency,status,transaction_ref,payment_type)
                       VALUES (%s,%s,%s,%s,'demo_paid',%s,'demo')""",
                    (student_id, item["id"], item["price"], item["currency"], f"DEMO-{uuid.uuid4().hex[:16].upper()}"),
                )
        _enroll(student_id, item["id"])
    execute("DELETE FROM academy_cart_items WHERE student_id=%s", (student_id,))
    flash("Demo checkout complete. No real payment was taken.", "success")
    return redirect(url_for("academy.learning"))


@academy_bp.route("/enroll/<int:course_id>", methods=["POST"])
@student_required
def enroll(course_id):
    course = query_one(
        """SELECT c.id,c.price FROM courses c WHERE c.id=%s AND c.status='published'
           AND EXISTS (SELECT 1 FROM academy_lessons l WHERE l.course_id=c.id)""",
        (course_id,),
    )
    if not course:
        abort(404)
    if Decimal(str(course.get("price") or 0)) > 0:
        return redirect(url_for("academy.demo_checkout", course_id=course_id))
    _enroll(session["academy_student_id"], course_id)
    flash("You’re enrolled. Start with the first lesson.", "success")
    first = query_one("SELECT id FROM academy_lessons WHERE course_id=%s ORDER BY sort_order,id LIMIT 1", (course_id,))
    if first:
        return redirect(url_for("academy.lesson", course_id=course_id, lesson_id=first["id"]))
    return redirect(url_for("academy.course_detail", course_id=course_id))


@academy_bp.route("/checkout/<int:course_id>", methods=["GET", "POST"])
@student_required
def demo_checkout(course_id):
    course = query_one(
        """SELECT c.* FROM courses c WHERE c.id=%s AND c.status='published'
           AND EXISTS (SELECT 1 FROM academy_lessons l WHERE l.course_id=c.id)""",
        (course_id,),
    )
    if not course:
        abort(404)
    if Decimal(str(course.get("price") or 0)) <= 0:
        return redirect(url_for("academy.course_detail", course_id=course_id))
    student_id = session["academy_student_id"]
    if request.method == "POST":
        existing = query_one(
            "SELECT id FROM academy_payments WHERE student_id=%s AND course_id=%s AND status='demo_paid' LIMIT 1",
            (student_id, course_id),
        )
        if not existing:
            reference = f"DEMO-{uuid.uuid4().hex[:16].upper()}"
            execute(
                """INSERT INTO academy_payments (student_id,course_id,amount,currency,status,transaction_ref,payment_type)
                   VALUES (%s,%s,%s,%s,'demo_paid',%s,'demo')""",
                (student_id, course_id, course["price"], course["currency"], reference),
            )
        _enroll(student_id, course_id)
        flash("Demo checkout complete. No real payment was taken.", "success")
        first = query_one("SELECT id FROM academy_lessons WHERE course_id=%s ORDER BY sort_order,id LIMIT 1", (course_id,))
        if first:
            return redirect(url_for("academy.lesson", course_id=course_id, lesson_id=first["id"]))
        return redirect(url_for("academy.learning"))
    return render_template("academy/demo_checkout.html", course=course)


@academy_bp.route("/my-learning")
@student_required
def learning():
    courses = query_all(
        """SELECT c.*, e.progress, e.status AS enrollment_status,
                  (SELECT COUNT(*) FROM academy_lessons l WHERE l.course_id=c.id) AS lesson_count
           FROM academy_enrollments e JOIN courses c ON c.id=e.course_id
           WHERE e.student_id=%s ORDER BY e.enrolled_at DESC""",
        (session["academy_student_id"],),
    )
    saved_courses = query_all(
        """SELECT c.*,a.is_liked,(SELECT COUNT(*) FROM academy_course_actions x WHERE x.course_id=c.id AND x.is_liked=1) AS like_count
           FROM academy_course_actions a JOIN courses c ON c.id=a.course_id
           WHERE a.student_id=%s AND a.is_saved=1 AND c.status='published' ORDER BY a.updated_at DESC""",
        (session["academy_student_id"],),
    )
    return render_template("academy/learning.html", courses=courses, saved_courses=saved_courses)


@academy_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>")
def lesson(course_id, lesson_id):
    course = query_one("SELECT * FROM courses WHERE id=%s AND status='published'", (course_id,))
    lesson_data = query_one("SELECT * FROM academy_lessons WHERE id=%s AND course_id=%s", (lesson_id, course_id))
    if not course or not lesson_data:
        abort(404)

    student_id = session.get("academy_student_id")
    enrollment = query_one(
        "SELECT * FROM academy_enrollments WHERE student_id=%s AND course_id=%s AND status IN ('active','completed')",
        (student_id, course_id),
    ) if student_id else None
    if not enrollment and not lesson_data.get("is_preview"):
        flash("Enroll in this course to watch the full lessons.", "error")
        return redirect(url_for("academy.course_detail", course_id=course_id))

    lessons = query_all(
        """SELECT l.*, (p.id IS NOT NULL) AS is_completed
           FROM academy_lessons l
           LEFT JOIN academy_lesson_progress p ON p.lesson_id=l.id AND p.student_id=%s
           WHERE l.course_id=%s ORDER BY l.sort_order,l.id""",
        (student_id or 0, course_id),
    )
    return render_template(
        "academy/lesson.html", course=course, lesson=lesson_data, lessons=lessons,
        enrollment=enrollment, embed_url=video_player_url(lesson_data["video_url"]),
        is_youtube_url=is_youtube_url(lesson_data["video_url"]),
    )


@academy_bp.route("/media/<filename>")
def lesson_media(filename):
    if not re.fullmatch(r"[a-f0-9-]{36}\.(?:mp4|webm|ogg|mov|m4v)", filename):
        abort(404)
    video_url = f"/academy/media/{filename}"
    lesson_row = query_one(
        """SELECT l.id,l.is_preview,l.course_id FROM academy_lessons l
           JOIN courses c ON c.id=l.course_id WHERE l.video_url=%s AND c.status='published'""",
        (video_url,),
    )
    if not lesson_row:
        abort(404)
    if not lesson_row["is_preview"]:
        student_id = session.get("academy_student_id")
        enrollment = query_one(
            "SELECT id FROM academy_enrollments WHERE student_id=%s AND course_id=%s AND status IN ('active','completed')",
            (student_id, lesson_row["course_id"]),
        ) if student_id else None
        if not enrollment:
            abort(403)
    path = os.path.join(current_app.instance_path, "academy_videos", filename)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, conditional=True, max_age=0)


@academy_bp.route("/courses/<int:course_id>/lessons/<int:lesson_id>/complete", methods=["POST"])
@student_required
def lesson_complete(course_id, lesson_id):
    enrollment = query_one(
        "SELECT * FROM academy_enrollments WHERE student_id=%s AND course_id=%s AND status='active'",
        (session["academy_student_id"], course_id),
    )
    lesson_data = query_one("SELECT id FROM academy_lessons WHERE id=%s AND course_id=%s", (lesson_id, course_id))
    if not enrollment or not lesson_data:
        abort(403)
    completed = query_one(
        "SELECT id FROM academy_lesson_progress WHERE student_id=%s AND lesson_id=%s",
        (session["academy_student_id"], lesson_id),
    )
    if not completed:
        execute(
            "INSERT INTO academy_lesson_progress (student_id,lesson_id) VALUES (%s,%s)",
            (session["academy_student_id"], lesson_id),
        )
    total = query_one("SELECT COUNT(*) AS c FROM academy_lessons WHERE course_id=%s", (course_id,))["c"]
    done = query_one(
        """SELECT COUNT(*) AS c FROM academy_lesson_progress p
           JOIN academy_lessons l ON l.id=p.lesson_id WHERE p.student_id=%s AND l.course_id=%s""",
        (session["academy_student_id"], course_id),
    )["c"]
    progress = int(done * 100 / total) if total else 0
    execute(
        "UPDATE academy_enrollments SET progress=%s,status=%s WHERE id=%s",
        (progress, "completed" if progress == 100 and total else "active", enrollment["id"]),
    )
    flash("Lesson marked complete.", "success")
    next_lesson = query_one(
        """SELECT l.id FROM academy_lessons l
           LEFT JOIN academy_lesson_progress p ON p.lesson_id=l.id AND p.student_id=%s
           WHERE l.course_id=%s AND p.id IS NULL ORDER BY l.sort_order,l.id LIMIT 1""",
        (session["academy_student_id"], course_id),
    )
    if next_lesson:
        return redirect(url_for("academy.lesson", course_id=course_id, lesson_id=next_lesson["id"]))
    return redirect(url_for("academy.learning"))


# Administrator curriculum management
@academy_bp.route("/panel/courses/<int:course_id>/lessons")
@admin_required
def lessons_list(course_id):
    course = query_one("SELECT * FROM courses WHERE id=%s", (course_id,))
    if not course:
        abort(404)
    lessons = query_all("SELECT * FROM academy_lessons WHERE course_id=%s ORDER BY sort_order,id", (course_id,))
    return render_template("academy/lessons_list.html", course=course, lessons=lessons)


@academy_bp.route("/panel/lessons")
@admin_required
def lessons_hub():
    search = (request.args.get("q") or "").strip()[:100]
    params = []
    where = ""
    if search:
        where = "WHERE l.title LIKE %s OR c.title LIKE %s"
        params = [f"%{search}%", f"%{search}%"]
    lessons = query_all(
        f"""SELECT l.*,c.title AS course_title,c.status AS course_status
            FROM academy_lessons l JOIN courses c ON c.id=l.course_id {where}
            ORDER BY c.sort_order,c.title,l.sort_order,l.id""",
        tuple(params),
    )
    return render_template("academy/lessons_hub.html", lessons=lessons, search=search)


@academy_bp.route("/panel/courses/<int:course_id>/lessons/new", methods=["GET", "POST"])
@academy_bp.route("/panel/courses/<int:course_id>/lessons/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def lesson_form(course_id, item_id=None):
    course = query_one("SELECT * FROM courses WHERE id=%s", (course_id,))
    lesson_data = query_one("SELECT * FROM academy_lessons WHERE id=%s AND course_id=%s", (item_id, course_id)) if item_id else None
    if not course:
        abort(404)
    if item_id and not lesson_data:
        abort(404)
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        video_url = (request.form.get("video_url") or "").strip()
        video_upload = request.files.get("video_file")
        duration = (request.form.get("duration") or "").strip()[:40]
        try:
            sort_order = int(request.form.get("sort_order") or 0)
        except ValueError:
            sort_order = 0
        sort_order = max(-999999, min(999999, sort_order))
        has_upload = bool(video_upload and video_upload.filename)
        if lesson_data and not video_url and not has_upload:
            video_url = lesson_data["video_url"]
        if not title or len(title) > 180 or (not has_upload and not valid_video_url(video_url)):
            flash("Enter a lesson title and either choose a supported video file or enter a secure video URL.", "error")
            return render_template("academy/lesson_form.html", course=course, lesson=lesson_data)
        old_video = lesson_data.get("video_url") if lesson_data else None
        if has_upload:
            try:
                video_url = save_academy_upload(video_upload, "lessons")
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("academy/lesson_form.html", course=course, lesson=lesson_data)
        values = (title, description, video_url, duration or None, sort_order, 1 if request.form.get("is_preview") else 0)
        if lesson_data:
            execute("""UPDATE academy_lessons SET title=%s,description=%s,video_url=%s,duration=%s,
                       sort_order=%s,is_preview=%s WHERE id=%s AND course_id=%s""", (*values, item_id, course_id))
            if old_video and old_video != video_url:
                delete_academy_upload(old_video, "lessons")
            flash("Lesson updated.", "success")
        else:
            execute("""INSERT INTO academy_lessons (course_id,title,description,video_url,duration,sort_order,is_preview)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""", (course_id, *values))
            flash("Lesson added.", "success")
        return redirect(url_for("academy.lessons_list", course_id=course_id))
    return render_template("academy/lesson_form.html", course=course, lesson=lesson_data)


@academy_bp.route("/panel/courses/<int:course_id>/lessons/<int:item_id>/delete", methods=["POST"])
@admin_required
def lesson_delete(course_id, item_id):
    lesson_row = query_one("SELECT video_url FROM academy_lessons WHERE id=%s AND course_id=%s", (item_id, course_id))
    if lesson_row:
        delete_academy_upload(lesson_row.get("video_url"), "lessons")
    execute("DELETE FROM academy_lesson_progress WHERE lesson_id=%s", (item_id,))
    execute("DELETE FROM academy_lessons WHERE id=%s AND course_id=%s", (item_id, course_id))
    flash("Lesson deleted.", "success")
    return redirect(url_for("academy.lessons_list", course_id=course_id))


@academy_bp.route("/panel/enrollments")
@admin_required
def enrollments_list():
    rows = query_all(
        """SELECT e.*,s.name AS student_name,s.email,c.title AS course_title
           FROM academy_enrollments e JOIN academy_students s ON s.id=e.student_id
           JOIN courses c ON c.id=e.course_id ORDER BY e.enrolled_at DESC"""
    )
    return render_template("academy/enrollments_list.html", enrollments=rows)


@academy_bp.route("/panel/enrollments/new", methods=["GET", "POST"])
@academy_bp.route("/panel/enrollments/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def enrollment_form(item_id=None):
    enrollment = query_one("SELECT * FROM academy_enrollments WHERE id=%s", (item_id,)) if item_id else None
    students = query_all("SELECT id,name,email FROM academy_students ORDER BY name,id")
    courses = query_all("SELECT id,title FROM courses ORDER BY title,id")
    if request.method == "POST":
        try:
            student_id = int(request.form.get("student_id") or 0)
            course_id = int(request.form.get("course_id") or 0)
            progress = max(0, min(100, int(request.form.get("progress") or 0)))
        except ValueError:
            student_id, course_id, progress = 0, 0, 0
        status = (request.form.get("status") or "active").strip()
        status = status if status in {"active", "paused", "completed", "cancelled"} else "active"
        if not query_one("SELECT id FROM academy_students WHERE id=%s", (student_id,)) or not query_one("SELECT id FROM courses WHERE id=%s", (course_id,)):
            flash("Choose an existing student and course.", "error")
        else:
            duplicate = query_one("SELECT id FROM academy_enrollments WHERE student_id=%s AND course_id=%s AND id<>%s", (student_id, course_id, item_id or 0))
            if duplicate:
                flash("That student is already enrolled in this course.", "error")
            else:
                if enrollment:
                    execute("UPDATE academy_enrollments SET student_id=%s,course_id=%s,status=%s,progress=%s WHERE id=%s", (student_id, course_id, status, progress, item_id))
                else:
                    execute("INSERT INTO academy_enrollments (student_id,course_id,status,progress) VALUES (%s,%s,%s,%s)", (student_id, course_id, status, progress))
                flash("Enrollment saved.", "success")
                return redirect(url_for("academy.enrollments_list"))
    return render_template("academy/enrollment_form.html", enrollment=enrollment, students=students, courses=courses)


@academy_bp.route("/panel/enrollments/<int:item_id>/delete", methods=["POST"])
@admin_required
def enrollment_delete(item_id):
    execute("DELETE FROM academy_enrollments WHERE id=%s", (item_id,))
    flash("Enrollment removed.", "success")
    return redirect(url_for("academy.enrollments_list"))


@academy_bp.route("/panel/payments")
@admin_required
def payments_list():
    search = (request.args.get("q") or "").strip()[:100]
    status = request.args.get("status", "all")
    clauses, params = ["p.payment_type='demo'"], []
    if search:
        clauses.append("(s.name LIKE %s OR s.email LIKE %s OR c.title LIKE %s OR p.transaction_ref LIKE %s)")
        params.extend([f"%{search}%"] * 4)
    if status in {"demo_paid", "refunded", "failed"}:
        clauses.append("p.status=%s")
        params.append(status)
    else:
        status = "all"
    payments = query_all(
        f"""SELECT p.*,s.name AS student_name,s.email,c.title AS course_title
            FROM academy_payments p JOIN academy_students s ON s.id=p.student_id
            LEFT JOIN courses c ON c.id=p.course_id WHERE {' AND '.join(clauses)}
            ORDER BY p.created_at DESC,p.id DESC""",
        tuple(params),
    )
    summary = query_all(
        """SELECT currency,COUNT(*) AS count,COALESCE(SUM(CASE WHEN status='demo_paid' THEN amount ELSE 0 END),0) AS total
           FROM academy_payments WHERE payment_type='demo' GROUP BY currency ORDER BY currency"""
    )
    payment_count = query_one("SELECT COUNT(*) AS c FROM academy_payments WHERE payment_type='demo'")["c"]
    return render_template("academy/payments_list.html", payments=payments, summary=summary, payment_count=payment_count,
                           search=search, status=status)


@academy_bp.route("/panel/payments/<int:item_id>/status", methods=["POST"])
@admin_required
def payment_status(item_id):
    payment = query_one("SELECT * FROM academy_payments WHERE id=%s AND payment_type='demo'", (item_id,))
    if not payment:
        abort(404)
    status = request.form.get("status")
    if status not in {"demo_paid", "refunded", "failed"}:
        abort(400)
    execute("UPDATE academy_payments SET status=%s WHERE id=%s", (status, item_id))
    if status in {"refunded", "failed"}:
        execute("UPDATE academy_enrollments SET status='cancelled' WHERE student_id=%s AND course_id=%s",
                (payment["student_id"], payment["course_id"]))
    elif status == "demo_paid":
        _enroll(payment["student_id"], payment["course_id"])
    flash(f"Demo payment marked {status.replace('_', ' ')}.", "success")
    return redirect(url_for("academy.payments_list"))
