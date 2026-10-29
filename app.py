"""ENGSAQAWE — Flask + MySQL portfolio with admin panel."""

import os
import secrets
import hashlib
import smtplib
import ssl
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import formataddr
from hmac import compare_digest
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, flash, redirect, url_for, abort, Response, jsonify, session, g
from xml.sax.saxutils import escape
from db_helpers import query_all, query_one, execute, execute_returning_id
from database import get_db
from werkzeug.security import check_password_hash, generate_password_hash
from seed_mysql import seed
from utils import tech_meta, demo_link, TECH_ICONS, cert_preview_href, cert_download_href
from site_settings import (
    get_site_settings,
    parse_pipe_lines,
    parse_filters,
    split_title,
)
from admin_routes import admin_bp
from academy_routes import academy_bp

app = Flask(__name__)
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
SECRET_KEY = os.getenv("SECRET_KEY")
try:
    ACADEMY_MAX_VIDEO_MB = max(16, min(1024, int(os.getenv("ACADEMY_MAX_VIDEO_MB", "256"))))
except ValueError:
    ACADEMY_MAX_VIDEO_MB = 256
if APP_ENV == "production" and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in production.")
app.secret_key = SECRET_KEY or secrets.token_hex(32)
app.config.update(
    MAX_CONTENT_LENGTH=(ACADEMY_MAX_VIDEO_MB + 2) * 1024 * 1024,
    ACADEMY_MAX_VIDEO_MB=ACADEMY_MAX_VIDEO_MB,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=(APP_ENV == "production"),
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)
VISITOR_TIMEZONE = ZoneInfo("Africa/Mogadishu")
VISITOR_COOKIE = "engsaqawe_visitor"
NOTIFICATION_EMAIL = "nuurc9399@gmail.com"


def send_message_notification(name, email, message, channel):
    """Send a best-effort Gmail notification using the project's local app password."""
    app_password = (os.getenv("app_password") or os.getenv("GMAIL_APP_PASSWORD") or "").replace(" ", "")
    if not app_password:
        app.logger.warning("Message notification skipped: Gmail app password is not configured.")
        return False
    sender_email = (os.getenv("GMAIL_ADDRESS") or os.getenv("SMTP_USERNAME") or NOTIFICATION_EMAIL).strip()
    sender_name = " ".join((os.getenv("app_name") or "ENGSAQAWE Portfolio").split())[:100] or "ENGSAQAWE Portfolio"
    display_name = " ".join((name or "Visitor").split())[:120]
    email_message = EmailMessage()
    email_message["Subject"] = f"New portfolio {channel} message from {display_name}"
    email_message["From"] = formataddr((sender_name, sender_email))
    email_message["To"] = NOTIFICATION_EMAIL
    email_message.set_content(
        f"A new message was sent through your portfolio {channel}.\n\n"
        f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}\n"
    )
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=8, context=ssl.create_default_context()) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(email_message)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        app.logger.warning("Portfolio message notification failed (%s).", type(exc).__name__)
        return False


@app.before_request
def limit_request_size():
    """Keep ordinary forms small while allowing bounded Academy video uploads."""
    content_length = request.content_length
    if not content_length:
        return None
    if request.endpoint == "academy.lesson_form" and request.method == "POST":
        max_bytes = (ACADEMY_MAX_VIDEO_MB + 2) * 1024 * 1024
    elif request.endpoint == "academy.course_form" and request.method == "POST":
        max_bytes = 10 * 1024 * 1024
    else:
        max_bytes = 8 * 1024 * 1024
    if content_length > max_bytes:
        abort(413, description=f"This upload exceeds the {max_bytes // (1024 * 1024)} MB limit.")
    return None


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


@app.context_processor
def expose_csrf_token():
    return {"csrf_token": csrf_token}


@app.before_request
def enforce_csrf():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    submitted = request.form.get("_csrf_token", "") or request.headers.get("X-CSRFToken", "")
    valid_tokens = (session.get("csrf_token", ""), session.get("blog_csrf_token", ""))
    if not any(token and compare_digest(submitted, token) for token in valid_tokens):
        abort(400, description="The form expired. Reload the page and try again.")
    return None


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    visitor_cookie = getattr(g, "visitor_cookie_to_set", None)
    if visitor_cookie:
        response.set_cookie(
            VISITOR_COOKIE,
            visitor_cookie,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            secure=(APP_ENV == "production"),
            samesite="Lax",
        )
    return response


@app.before_request
def record_unique_public_visitor():
    """Count distinct browser cookies once per Mogadishu calendar day."""
    if request.method != "GET" or request.endpoint in {"static", "chat_messages"}:
        return None
    if request.path.startswith("/admin/") or session.get("admin_id"):
        return None
    user_agent = (request.headers.get("User-Agent") or "").casefold()
    if any(token in user_agent for token in ("bot", "crawler", "spider", "slurp", "preview")):
        return None
    visitor_cookie = request.cookies.get(VISITOR_COOKIE)
    if not visitor_cookie or len(visitor_cookie) > 100:
        visitor_cookie = secrets.token_urlsafe(32)
        g.visitor_cookie_to_set = visitor_cookie
    visitor_key = hashlib.sha256(visitor_cookie.encode("utf-8")).hexdigest()
    local_now = datetime.now(VISITOR_TIMEZONE).replace(tzinfo=None)
    local_today = local_now.date()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO visitor_registry (visitor_key,first_seen_at,last_seen_at) VALUES (%s,%s,%s)
                   ON DUPLICATE KEY UPDATE last_seen_at=VALUES(last_seen_at)""",
                (visitor_key, local_now, local_now),
            )
            cur.execute(
                "INSERT IGNORE INTO visitor_daily_visits (visitor_key,visit_date,first_visit_at) VALUES (%s,%s,%s)",
                (visitor_key, local_today, local_now),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return None

app.jinja_env.globals.update(
    tech_meta=tech_meta,
    demo_link=demo_link,
    cert_preview_href=cert_preview_href,
    cert_download_href=cert_download_href,
    tech_icons=TECH_ICONS,
    split_title=split_title,
)

app.register_blueprint(admin_bp)
app.register_blueprint(academy_bp)


def social_icon(label, url=""):
    value = f"{label or ''} {url or ''}".casefold()
    icons = (
        (("github",), "fa-brands fa-github"),
        (("linkedin",), "fa-brands fa-linkedin"),
        (("facebook",), "fa-brands fa-facebook"),
        (("instagram",), "fa-brands fa-instagram"),
        (("youtube",), "fa-brands fa-youtube"),
        (("whatsapp", "wa.me"), "fa-brands fa-whatsapp"),
        (("twitter", "x.com", "x-twitter"), "fa-brands fa-x-twitter"),
        (("telegram", "t.me"), "fa-brands fa-telegram"),
        (("tiktok",), "fa-brands fa-tiktok"),
        (("discord",), "fa-brands fa-discord"),
        (("medium",), "fa-brands fa-medium"),
    )
    for needles, icon in icons:
        if any(needle in value for needle in needles):
            return icon
    return "fa-solid fa-link"


app.jinja_env.globals.update(social_icon=social_icon)

# Keep newly added CMS tables available on deployed WSGI servers as well as local runs.
try:
    seed()
except Exception as exc:
    app.logger.warning("Database initialization deferred: %s", exc)


def get_gallery():
    rows = query_all("SELECT * FROM gallery ORDER BY sort_order ASC, id ASC")
    if rows:
        return rows
    return [
        {"image_url": "images/pictures/me.png", "label": "Portrait", "is_hero": 1},
        {"image_url": "images/pictures/me2.png", "label": "Portrait 2", "is_hero": 0},
    ]


def get_hero_image(profile, gallery):
    if profile and profile.get("hero_image"):
        return profile["hero_image"]
    for item in gallery:
        if item.get("is_hero"):
            return item["image_url"]
    return gallery[0]["image_url"] if gallery else "images/pictures/me.png"


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        user_id = session.get("site_user_id")
        if not user_id:
            if wants_json:
                return jsonify({"ok": False, "message": "Sign in before sending a message."}), 401
            flash("Please sign in or create an account before sending a message.", "error")
            return redirect(url_for("account_login", next="/#contact"))
        user = query_one("SELECT id, name, email FROM site_users WHERE id=%s AND is_active=1", (user_id,))
        if not user:
            session.pop("site_user_id", None)
            session.pop("site_user_name", None)
            session.pop("site_user_email", None)
            if wants_json:
                return jsonify({"ok": False, "message": "Please sign in again."}), 401
            return redirect(url_for("account_login", next="/#contact"))
        name, email = user["name"], user["email"]
        project_type = (request.form.get("projectType") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not name or not email or not message:
            if wants_json:
                return jsonify({"ok": False, "message": "Please enter a message."}), 400
            flash("Please fill in all required fields.", "error")
        elif len(project_type) > 80:
            if wants_json:
                return jsonify({"ok": False, "message": "Please choose a valid project type."}), 400
            flash("Please choose a valid project type.", "error")
        elif len(message) > 250:
            if wants_json:
                return jsonify({"ok": False, "message": "Messages must be 250 characters or fewer."}), 400
            flash("Messages must be 250 characters or fewer.", "error")
        else:
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO contacts (name, email, project_type, message) VALUES (%s,%s,%s,%s)",
                                (name, email, project_type or None, message))
                    cur.execute("INSERT INTO site_chats (user_id) VALUES (%s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)", (user_id,))
                    chat_id = cur.lastrowid
                    cur.execute("INSERT INTO site_chat_messages (chat_id,sender_type,sender_id,body) VALUES (%s,'user',%s,%s)",
                                (chat_id, user_id, message))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            send_message_notification(name, email, message, "contact")
            if wants_json:
                return jsonify({"ok": True, "message": "Your message was sent. I’ll reply in the chat panel."}), 201
            flash("Message saved. I will get back to you soon.", "success")
            return redirect(url_for("home") + "#contact")

    profile = query_one("SELECT * FROM profile WHERE id = 1")
    settings = get_site_settings()
    projects = query_all("SELECT * FROM projects WHERE featured = 1 ORDER BY sort_order ASC, id ASC")
    services = query_all("SELECT * FROM services WHERE is_active = 1 ORDER BY sort_order ASC, id ASC")
    footer_projects = query_all("SELECT title, live_link FROM projects ORDER BY sort_order ASC, id ASC LIMIT 5")
    certificates = query_all("SELECT * FROM certificates ORDER BY sort_order ASC, id ASC")
    courses = query_all(
        """SELECT c.*, (SELECT COUNT(*) FROM academy_lessons l WHERE l.course_id=c.id) AS lesson_count
           FROM courses c WHERE c.status='published' ORDER BY c.sort_order ASC, c.id ASC"""
    )
    blog_posts = query_all("SELECT id, title, slug, excerpt, cover_image, category, author, published_at FROM blog_posts WHERE status = 'published' ORDER BY published_at DESC, id DESC LIMIT 3")
    research_items = query_all("SELECT * FROM research_items WHERE is_published=1 ORDER BY sort_order ASC, published_on DESC, id DESC")
    footer_links = query_all("SELECT * FROM footer_links WHERE is_active = 1 ORDER BY section_order ASC, sort_order ASC, id ASC")
    affiliate_links = []
    affiliate_urls = set()
    affiliate_group_names = {"affiliate links", "affiliates"}
    for item in footer_links:
        if (item.get("section_title") or "").strip().casefold() not in affiliate_group_names:
            continue
        destination = (item.get("url") or "").strip().rstrip("/").casefold()
        if destination and destination in affiliate_urls:
            continue
        if destination:
            affiliate_urls.add(destination)
        affiliate_links.append(item)
    footer_link_groups = {}
    social_group_names = {"social", "social links"}
    for item in footer_links:
        group_name = " ".join((item.get("section_title") or "").casefold().split())
        if group_name in affiliate_group_names | social_group_names | {"selected projects"}:
            continue
        footer_link_groups.setdefault(item["section_title"], []).append(item)
    footer_social_links = [
        {"label": item["label"], "url": item["url"], "icon": social_icon(item["label"], item["url"])}
        for item in footer_links
        if " ".join((item.get("section_title") or "").casefold().split()) in social_group_names
    ]
    if not footer_social_links:
        social_fields = (
            ("GitHub", "github_url"), ("LinkedIn", "linkedin_url"),
            ("Facebook", "facebook_url"), ("YouTube", "youtube_url"),
            ("X / Twitter", "twitter_url"),
        )
        for label, field in social_fields:
            destination = (profile or {}).get(field)
            if destination:
                footer_social_links.append({"label": label, "url": destination, "icon": social_icon(label, destination)})
        phone = (profile or {}).get("whatsapp") or "684421687"
        country_code = settings.get("whatsapp_country_code", "252") or "252"
        footer_social_links.append({
            "label": "WhatsApp",
            "url": f"https://wa.me/{country_code}{phone}",
            "icon": social_icon("WhatsApp", "wa.me"),
        })
    gallery = get_gallery()
    hero_image = get_hero_image(profile, gallery)
    skills_cards = [
        {"icon": icon or "fa-code", "title": title, "text": text}
        for icon, title, text in parse_pipe_lines(settings.get("skills_cards", ""), 3)
    ]
    timeline_items = [
        {"title": title, "meta": meta, "body": body}
        for title, meta, body in parse_pipe_lines(settings.get("timeline_items", ""), 3)
    ]
    portfolio_filters = parse_filters(settings.get("portfolio_filters", ""))
    tech_list = [t.strip() for t in (settings.get("tech_list") or "").split(",") if t.strip()]
    project_type_options = [
        line.strip()
        for line in (settings.get("project_type_options") or "").splitlines()
        if line.strip()
    ]
    service_titles = [service["title"] for service in services]
    service_title_set = set(service_titles)
    project_type_options = service_titles + [option for option in project_type_options if option not in service_title_set]
    typewriter_phrases = [
        line.strip()
        for line in (settings.get("typewriter_phrases") or "").splitlines()
        if line.strip()
    ]

    return render_template(
        "index.html",
        profile=profile,
        projects=projects,
        services=services,
        affiliate_links=affiliate_links,
        footer_projects=footer_projects,
        certificates=certificates,
        courses=courses,
        blog_posts=blog_posts,
        research_items=research_items,
        site_user=session.get("site_user_id"),
        site_chat_messages=(query_all("""SELECT m.sender_type,m.body,m.created_at FROM site_chat_messages m
            JOIN site_chats c ON c.id=m.chat_id WHERE c.user_id=%s ORDER BY m.id ASC""", (session["site_user_id"],)) if session.get("site_user_id") else []),
        footer_links=footer_links,
        footer_link_groups=footer_link_groups.items(),
        footer_social_links=footer_social_links,
        gallery=gallery,
        hero_image=hero_image,
        settings=settings,
        skills_cards=skills_cards,
        timeline_items=timeline_items,
        portfolio_filters=portfolio_filters,
        tech_list=tech_list,
        project_type_options=project_type_options,
        typewriter_phrases=typewriter_phrases,
        tech_meta=tech_meta,
        demo_link=demo_link,
        cert_preview_href=cert_preview_href,
        cert_download_href=cert_download_href,
        tech_icons=TECH_ICONS,
    )


def safe_local_next(value, fallback="/"):
    value = (value or "").strip()
    parsed = urlsplit(value)
    return value if value.startswith("/") and not value.startswith("//") and not parsed.netloc else fallback


@app.route("/account/register", methods=["GET", "POST"])
def account_register():
    next_url = safe_local_next(request.values.get("next"), "/#contact")
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        email_shape_ok = email.count("@") == 1 and "." in email.rsplit("@", 1)[-1] and not any(char.isspace() for char in email)
        if len(name) < 2 or len(name) > 120 or len(email) > 180 or not email_shape_ok or len(password) < 10 or len(password) > 256:
            flash("Enter your name, a valid email, and a password with at least 10 characters.", "error")
        elif query_one("SELECT id FROM site_users WHERE email=%s", (email,)):
            flash("An account with that email already exists. Please sign in.", "error")
            return redirect(url_for("account_login", next=next_url))
        else:
            try:
                account_id = execute_returning_id(
                    "INSERT INTO site_users (name,email,password_hash) VALUES (%s,%s,%s)",
                    (name, email, generate_password_hash(password)),
                )
                session.clear()
                session.permanent = True
                session["site_user_id"], session["site_user_name"], session["site_user_email"] = account_id, name, email
                return redirect(next_url)
            except Exception:
                flash("That account could not be created. Please try signing in or use another email.", "error")
    return render_template("account_auth.html", mode="register", next_url=next_url)


@app.route("/account/login", methods=["GET", "POST"])
def account_login():
    next_url = safe_local_next(request.values.get("next"), "/#contact")
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = query_one("SELECT id,name,email,password_hash FROM site_users WHERE email=%s AND is_active=1", (email,))
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Email or password is incorrect.", "error")
        else:
            session.clear()
            session.permanent = True
            session["site_user_id"], session["site_user_name"], session["site_user_email"] = user["id"], user["name"], user["email"]
            return redirect(next_url)
    return render_template("account_auth.html", mode="login", next_url=next_url)


@app.route("/account/logout", methods=["POST"])
def account_logout():
    if not session.get("site_user_id"):
        abort(403)
    session.pop("site_user_id", None)
    session.pop("site_user_name", None)
    session.pop("site_user_email", None)
    flash("You have signed out.", "success")
    return redirect(url_for("home"))


@app.route("/chat/send", methods=["POST"])
def chat_send():
    wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    user_id = session.get("site_user_id")
    if not user_id:
        if wants_json:
            return jsonify({"ok": False, "message": "Sign in before sending a chat message."}), 401
        return redirect(url_for("account_login", next="/#chat-widget"))
    user = query_one("SELECT id,name,email FROM site_users WHERE id=%s AND is_active=1", (user_id,))
    if not user:
        session.pop("site_user_id", None)
        if wants_json:
            return jsonify({"ok": False, "message": "Please sign in again."}), 401
        return redirect(url_for("account_login", next="/#chat-widget"))
    message = (request.form.get("message") or "").strip()
    if not message or len(message) > 2000:
        if wants_json:
            return jsonify({"ok": False, "message": "Chat messages must be between 1 and 2,000 characters."}), 400
        flash("Chat messages must be between 1 and 2,000 characters.", "error")
        return redirect(url_for("home") + "#chat-widget")
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO site_chats (user_id) VALUES (%s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)", (user_id,))
            chat_id = cur.lastrowid
            cur.execute("INSERT INTO site_chat_messages (chat_id,sender_type,sender_id,body) VALUES (%s,'user',%s,%s)", (chat_id,user_id,message))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    send_message_notification(user["name"], user["email"], message, "chat")
    if wants_json:
        return jsonify({"ok": True, "message": "Message sent."}), 201
    return redirect(url_for("home") + "#chat-widget")


@app.route("/chat/messages")
def chat_messages():
    user_id = session.get("site_user_id")
    if not user_id:
        return jsonify({"error": "sign_in_required"}), 401
    rows = query_all("""SELECT m.sender_type,m.body,m.created_at FROM site_chat_messages m
        JOIN site_chats c ON c.id=m.chat_id WHERE c.user_id=%s ORDER BY m.id ASC""", (user_id,))
    return jsonify([{"sender": row["sender_type"], "body": row["body"], "created_at": str(row["created_at"])} for row in rows])


@app.route("/blog")
def blog_index():
    posts = query_all("SELECT * FROM blog_posts WHERE status = 'published' ORDER BY published_at DESC, id DESC")
    settings = get_site_settings()
    return render_template("blog/index.html", posts=posts, settings=settings)


def blog_visitor_key():
    """Return a stable, anonymous browser key for article views and reactions."""
    if not session.get("blog_visitor_key"):
        session["blog_visitor_key"] = secrets.token_hex(32)
    return session["blog_visitor_key"]


@app.route("/blog/<slug>", methods=["GET", "POST"])
def blog_post(slug):
    post = query_one("SELECT * FROM blog_posts WHERE slug = %s AND status = 'published'", (slug,))
    if not post:
        abort(404)
    if not session.get("blog_csrf_token"):
        session["blog_csrf_token"] = secrets.token_urlsafe(32)
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token", "")
        if not secrets.compare_digest(submitted_token, session.get("blog_csrf_token", "")):
            abort(400)
        name = (request.form.get("name") or "").strip()
        body = (request.form.get("comment") or "").strip()
        if not 2 <= len(name) <= 80 or not 3 <= len(body) <= 1200:
            flash("Enter a name (2–80 characters) and comment (3–1200 characters).", "error")
        else:
            execute("INSERT INTO blog_comments (post_id, name, body, status) VALUES (%s, %s, %s, 'pending')",
                    (post["id"], name, body))
            flash("Thanks! Your comment is awaiting review.", "success")
        return redirect(url_for("blog_post", slug=slug) + "#comments")

    visitor_key = blog_visitor_key()
    execute("INSERT IGNORE INTO blog_post_views (post_id, visitor_key) VALUES (%s, %s)", (post["id"], visitor_key))
    views = query_one("SELECT COUNT(*) AS total FROM blog_post_views WHERE post_id = %s", (post["id"],))["total"]
    reaction_rows = query_all("SELECT reaction, COUNT(*) AS total FROM blog_post_reactions WHERE post_id = %s GROUP BY reaction", (post["id"],))
    reactions = {row["reaction"]: row["total"] for row in reaction_rows}
    my_reaction = query_one("SELECT reaction FROM blog_post_reactions WHERE post_id = %s AND visitor_key = %s", (post["id"], visitor_key))
    comments = query_all("SELECT name, body, created_at FROM blog_comments WHERE post_id = %s AND status = 'approved' ORDER BY created_at DESC", (post["id"],))
    settings = get_site_settings()
    return render_template("blog/post.html", post=post, settings=settings, views=views,
                           reactions=reactions, my_reaction=my_reaction["reaction"] if my_reaction else "",
                           comments=comments)


@app.route("/blog/<slug>/react", methods=["POST"])
def blog_react(slug):
    post = query_one("SELECT id FROM blog_posts WHERE slug = %s AND status = 'published'", (slug,))
    if not post:
        abort(404)
    reaction = (request.get_json(silent=True) or {}).get("reaction", "")
    csrf_token = request.headers.get("X-CSRFToken", "")
    if not secrets.compare_digest(csrf_token, session.get("blog_csrf_token", "")):
        return jsonify(error="Refresh the page and try again."), 400
    if reaction not in {"like", "dislike"}:
        return jsonify(error="Choose like or dislike."), 400
    visitor_key = blog_visitor_key()
    execute("""INSERT INTO blog_post_reactions (post_id, visitor_key, reaction) VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE reaction=VALUES(reaction)""", (post["id"], visitor_key, reaction))
    rows = query_all("SELECT reaction, COUNT(*) AS total FROM blog_post_reactions WHERE post_id = %s GROUP BY reaction", (post["id"],))
    counts = {row["reaction"]: row["total"] for row in rows}
    return jsonify(likes=counts.get("like", 0), dislikes=counts.get("dislike", 0), reaction=reaction)


@app.route("/robots.txt")
def robots():
    from flask import send_from_directory
    return send_from_directory(app.root_path, "robots.txt")


@app.route("/sitemap.xml")
def sitemap():
    base = (get_site_settings().get("site_url") or "https://engsaqawe.com").rstrip("/")
    posts = query_all("SELECT slug, updated_at FROM blog_posts WHERE status = 'published' ORDER BY published_at DESC")
    urls = [f"{base}/", f"{base}/blog"]
    for post in posts:
        lastmod = post.get("updated_at")
        if hasattr(lastmod, "strftime"):
            lastmod = lastmod.strftime("%Y-%m-%d")
        urls.append((f"{base}/blog/{post['slug']}", lastmod or ""))
    entries = []
    for item in urls:
        loc, lastmod = item if isinstance(item, tuple) else (item, "")
        lastmod_xml = f"<lastmod>{escape(str(lastmod))}</lastmod>" if lastmod else ""
        entries.append(f"<url><loc>{escape(loc)}</loc>{lastmod_xml}</url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(entries) + "</urlset>"
    return Response(xml, mimetype="application/xml; charset=utf-8")


if __name__ == "__main__":
    app.run(debug=(APP_ENV != "production"), host="127.0.0.1", port=5000)
