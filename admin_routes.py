"""Admin panel routes — login and full content management."""

import os
import re
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from auth import admin_required, login_admin, get_admin_by_id
from db_helpers import query_all, query_one, execute, execute_returning_id
from database import get_db
from uploads import save_upload

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def safe_affiliate_destination(value):
    value = (value or "").strip()
    if not value or "\\" in value or any(ord(char) < 32 for char in value):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return ((parsed.scheme in {"http", "https"} and parsed.netloc and
             not parsed.username and not parsed.password) or
            (value.startswith("/") and not value.startswith("//")))


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        admin = login_admin(username, password)
        if admin:
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            flash("Welcome back.", "success")
            nxt = request.args.get("next") or request.form.get("next") or ""
            if nxt.startswith("/") and not nxt.startswith("//") and "\\" not in nxt:
                return redirect(nxt)
            return redirect(url_for("admin.dashboard"))
        flash("Wrong username or password.", "error")

    return render_template("admin/login.html")


@admin_bp.route("/logout", methods=["POST"])
@admin_required
def logout():
    session.clear()
    flash("You logged out.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_required
def dashboard():
    today = datetime.now(ZoneInfo("Africa/Mogadishu")).date()
    stats = {
        "projects": query_one("SELECT COUNT(*) AS c FROM projects")["c"],
        "services": query_one("SELECT COUNT(*) AS c FROM services")["c"],
        "blog": query_one("SELECT COUNT(*) AS c FROM blog_posts")["c"],
        "certificates": query_one("SELECT COUNT(*) AS c FROM certificates")["c"],
        "courses": query_one("SELECT COUNT(*) AS c FROM courses")["c"],
        "gallery": query_one("SELECT COUNT(*) AS c FROM gallery")["c"],
        "contacts": query_one("SELECT COUNT(*) AS c FROM contacts")["c"],
        "unread_contacts": query_one("SELECT COUNT(*) AS c FROM contacts")["c"],
        "visitors_today": query_one("SELECT COUNT(*) AS c FROM visitor_daily_visits WHERE visit_date=%s", (today,))["c"],
        "visitors_total": query_one("SELECT COUNT(*) AS c FROM visitor_registry")["c"],
    }
    recent_contacts = query_all(
        "SELECT * FROM contacts ORDER BY created_at DESC LIMIT 5"
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_contacts=recent_contacts,
        admin=get_admin_by_id(session["admin_id"]),
    )


# ---------- Profile ----------
@admin_bp.route("/profile", methods=["GET", "POST"])
@admin_required
def profile_edit():
    profile = query_one("SELECT * FROM profile WHERE id = 1")

    if request.method == "POST":
        fields = [
            "full_name", "brand_name", "tagline", "hero_title", "hero_subtitle",
            "mission", "vision", "location_note", "email", "whatsapp",
            "github_url", "linkedin_url", "twitter_url", "facebook_url", "youtube_url",
        ]
        values = [(request.form.get(f) or "").strip() for f in fields]
        hero_image = profile.get("hero_image") if profile else None

        if request.files.get("hero_image") and request.files["hero_image"].filename:
            try:
                hero_image = save_upload(request.files["hero_image"], current_app.root_path)
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("admin/profile_form.html", profile=profile)

        execute(
            """UPDATE profile SET
               full_name=%s, brand_name=%s, tagline=%s, hero_title=%s, hero_subtitle=%s,
               mission=%s, vision=%s, location_note=%s, email=%s, whatsapp=%s,
               github_url=%s, linkedin_url=%s, twitter_url=%s, facebook_url=%s, youtube_url=%s,
               hero_image=%s WHERE id=1""",
            (*values, hero_image),
        )
        flash("Profile updated.", "success")
        return redirect(url_for("admin.profile_edit"))

    return render_template("admin/profile_form.html", profile=profile)


# ---------- Site Settings (all public text) ----------
@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def site_settings():
    from site_settings import get_site_settings, save_site_settings, schema_by_group

    if request.method == "POST":
        save_site_settings(request.form)
        flash("Site settings saved. Refresh the public site to see changes.", "success")
        return redirect(url_for("admin.site_settings"))

    settings = get_site_settings()
    groups = schema_by_group()
    return render_template("admin/settings_form.html", settings=settings, groups=groups)


# ---------- Projects ----------
@admin_bp.route("/projects")
@admin_required
def projects_list():
    projects = query_all("SELECT * FROM projects ORDER BY sort_order ASC, id ASC")
    return render_template("admin/projects_list.html", projects=projects)


@admin_bp.route("/projects/new", methods=["GET", "POST"])
@admin_bp.route("/projects/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def project_form(item_id=None):
    project = query_one("SELECT * FROM projects WHERE id = %s", (item_id,)) if item_id else None

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        if not title:
            flash("Title is required.", "error")
            return render_template("admin/project_form.html", project=project)

        data = {
            "title": title,
            "description": (request.form.get("description") or "").strip(),
            "features": (request.form.get("features") or "").strip(),
            "challenges": (request.form.get("challenges") or "").strip(),
            "solutions": (request.form.get("solutions") or "").strip(),
            "tech_stack": (request.form.get("tech_stack") or "").strip(),
            "category": (request.form.get("category") or "saas").strip(),
            "live_link": (request.form.get("live_link") or "").strip(),
            "source_link": (request.form.get("source_link") or "").strip(),
            "sort_order": int(request.form.get("sort_order") or 0),
            "featured": 1 if request.form.get("featured") else 0,
            "image_url": project["image_url"] if project else "images/pictures/3.png",
        }

        if request.files.get("image") and request.files["image"].filename:
            try:
                data["image_url"] = save_upload(request.files["image"], current_app.root_path)
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("admin/project_form.html", project=project)

        row = (
            data["title"],
            data["description"],
            data["features"],
            data["challenges"],
            data["solutions"],
            data["tech_stack"],
            data["category"],
            data["image_url"],
            data["live_link"],
            data["source_link"],
            data["sort_order"],
            data["featured"],
        )

        if project:
            execute(
                """UPDATE projects SET title=%s, description=%s, features=%s, challenges=%s,
                   solutions=%s, tech_stack=%s, category=%s, image_url=%s, live_link=%s,
                   source_link=%s, sort_order=%s, featured=%s WHERE id=%s""",
                (*row, item_id),
            )
            flash("Project updated.", "success")
        else:
            execute(
                """INSERT INTO projects
                   (title, description, features, challenges, solutions, tech_stack, category,
                    image_url, live_link, source_link, sort_order, featured)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                row,
            )
            flash("Project created.", "success")
        return redirect(url_for("admin.projects_list"))

    return render_template("admin/project_form.html", project=project)


@admin_bp.route("/projects/<int:item_id>/delete", methods=["POST"])
@admin_required
def project_delete(item_id):
    execute("DELETE FROM projects WHERE id = %s", (item_id,))
    flash("Project deleted.", "success")
    return redirect(url_for("admin.projects_list"))


# ---------- Services ----------
def service_slug(value):
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")[:120]


def safe_service_cta(value):
    value = (value or "").strip()
    if not value or "\\" in value or value.startswith("//") or any(ord(char) < 32 for char in value):
        return False
    if value.startswith("#") or value.startswith("/"):
        return True
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


@admin_bp.route("/services")
@admin_required
def services_list():
    services = query_all("SELECT * FROM services ORDER BY sort_order ASC, id ASC")
    return render_template("admin/services_list.html", services=services)


@admin_bp.route("/services/new", methods=["GET", "POST"])
@admin_bp.route("/services/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def service_form(item_id=None):
    service = query_one("SELECT * FROM services WHERE id = %s", (item_id,)) if item_id else None
    art_types = ["web", "stack", "lang", "net", "learn"]

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        slug = service_slug(request.form.get("slug") or title)
        icon_class = (request.form.get("icon_class") or "").strip()
        accent_color = (request.form.get("accent_color") or "").strip()
        cta_url = (request.form.get("cta_url") or "").strip()
        art_type = (request.form.get("art_type") or "web").strip()
        try:
            sort_order = int(request.form.get("sort_order") or 0)
        except ValueError:
            sort_order = 0

        valid_icon = bool(re.fullmatch(r"fa-(?:solid|regular|brands|light|thin|duotone)(?:\s+fa-[a-z0-9-]+)+", icon_class))
        if (not title or len(title) > 160 or not description or not slug or len(slug) > 120
                or not valid_icon or not re.fullmatch(r"#[0-9a-fA-F]{6}", accent_color)
                or art_type not in art_types or len(cta_url) > 500 or not safe_service_cta(cta_url)):
            flash("Check the title, description, icon classes, six-digit accent color, visual type, and CTA URL.", "error")
            return render_template("admin/service_form.html", service=service, art_types=art_types)

        collision = query_one("SELECT id FROM services WHERE slug = %s AND id <> %s", (slug, item_id or 0))
        if collision:
            flash("That service slug is already in use. Choose a different slug.", "error")
            return render_template("admin/service_form.html", service=service, art_types=art_types)

        values = (
            slug, title, description, icon_class, accent_color,
            (request.form.get("tags") or "").strip(),
            (request.form.get("cta_label") or "Let’s talk").strip()[:120] or "Let’s talk",
            cta_url, art_type, sort_order, 1 if request.form.get("is_active") else 0,
        )
        if service:
            execute(
                """UPDATE services SET slug=%s, title=%s, description=%s, icon_class=%s,
                   accent_color=%s, tags=%s, cta_label=%s, cta_url=%s, art_type=%s,
                   sort_order=%s, is_active=%s WHERE id=%s""",
                (*values, item_id),
            )
            flash("Service updated.", "success")
        else:
            execute(
                """INSERT INTO services
                   (slug, title, description, icon_class, accent_color, tags, cta_label, cta_url, art_type, sort_order, is_active)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                values,
            )
            flash("Service added.", "success")
        return redirect(url_for("admin.services_list"))

    return render_template("admin/service_form.html", service=service, art_types=art_types)


@admin_bp.route("/services/<int:item_id>/delete", methods=["POST"])
@admin_required
def service_delete(item_id):
    execute("DELETE FROM services WHERE id = %s", (item_id,))
    flash("Service deleted.", "success")
    return redirect(url_for("admin.services_list"))


# ---------- Certificates ----------
@admin_bp.route("/certificates")
@admin_required
def certificates_list():
    items = query_all("SELECT * FROM certificates ORDER BY sort_order ASC, id ASC")
    return render_template("admin/certificates_list.html", certificates=items)


@admin_bp.route("/certificates/new", methods=["GET", "POST"])
@admin_bp.route("/certificates/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def certificate_form(item_id=None):
    cert = query_one("SELECT * FROM certificates WHERE id = %s", (item_id,)) if item_id else None

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        if not title:
            flash("Title is required.", "error")
            return render_template("admin/certificate_form.html", certificate=cert)

        image_url = cert["image_url"] if cert else "images/pictures/certi1.jpg"
        if request.files.get("image") and request.files["image"].filename:
            try:
                image_url = save_upload(request.files["image"], current_app.root_path)
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("admin/certificate_form.html", certificate=cert)

        try:
            sort_order = int(request.form.get("sort_order") or 0)
        except ValueError:
            flash("Display rank must be a whole number.", "error")
            return render_template("admin/certificate_form.html", certificate=cert)
        if sort_order <= 0:
            current = query_one("SELECT COALESCE(MAX(sort_order), 0) AS top_rank FROM certificates WHERE id <> %s", (item_id or 0,))
            sort_order = (current or {}).get("top_rank", 0) + 1

        payload = (
            title,
            (request.form.get("issuer") or "Independent").strip() or "Independent",
            (request.form.get("year") or "Not specified").strip() or "Not specified",
            (request.form.get("description") or "").strip(),
            image_url,
            (request.form.get("preview_url") or "").strip() or None,
            (request.form.get("download_url") or "").strip() or None,
            sort_order,
        )

        if cert:
            execute(
                """UPDATE certificates SET title=%s, issuer=%s, year=%s, description=%s,
                   image_url=%s, preview_url=%s, download_url=%s, sort_order=%s WHERE id=%s""",
                (*payload, item_id),
            )
            flash("Certificate updated.", "success")
        else:
            execute(
                """INSERT INTO certificates
                   (title, issuer, year, description, image_url, preview_url, download_url, sort_order)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                payload,
            )
            flash("Certificate created.", "success")
        return redirect(url_for("admin.certificates_list"))

    return render_template("admin/certificate_form.html", certificate=cert)


@admin_bp.route("/certificates/<int:item_id>/delete", methods=["POST"])
@admin_required
def certificate_delete(item_id):
    execute("DELETE FROM certificates WHERE id = %s", (item_id,))
    flash("Certificate deleted.", "success")
    return redirect(url_for("admin.certificates_list"))


# ---------- Courses ----------
@admin_bp.route("/courses")
@admin_required
def courses_list():
    items = query_all("SELECT * FROM courses ORDER BY sort_order ASC, id ASC")
    return render_template("admin/courses_list.html", courses=items)


@admin_bp.route("/courses/new", methods=["GET", "POST"])
@admin_bp.route("/courses/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def course_form(item_id=None):
    course = query_one("SELECT * FROM courses WHERE id = %s", (item_id,)) if item_id else None

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        if not title:
            flash("Title is required.", "error")
            return render_template("admin/course_form.html", course=course)

        payload = (
            title,
            (request.form.get("description") or "").strip(),
            (request.form.get("modules") or "").strip(),
            int(request.form.get("progress") or 0),
            (request.form.get("icon") or "fa-code").strip(),
            int(request.form.get("sort_order") or 0),
        )

        if course:
            execute(
                """UPDATE courses SET title=%s, description=%s, modules=%s,
                   progress=%s, icon=%s, sort_order=%s WHERE id=%s""",
                (*payload, item_id),
            )
            flash("Course updated.", "success")
        else:
            execute(
                """INSERT INTO courses (title, description, modules, progress, icon, sort_order)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                payload,
            )
            flash("Course created.", "success")
        return redirect(url_for("admin.courses_list"))

    return render_template("admin/course_form.html", course=course)


@admin_bp.route("/courses/<int:item_id>/delete", methods=["POST"])
@admin_required
def course_delete(item_id):
    execute("DELETE FROM courses WHERE id = %s", (item_id,))
    flash("Course deleted.", "success")
    return redirect(url_for("admin.courses_list"))


# ---------- Gallery / Photos ----------
@admin_bp.route("/gallery")
@admin_required
def gallery_list():
    items = query_all("SELECT * FROM gallery ORDER BY sort_order ASC, id ASC")
    return render_template("admin/gallery_list.html", gallery=items)


@admin_bp.route("/gallery/new", methods=["GET", "POST"])
@admin_bp.route("/gallery/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def gallery_form(item_id=None):
    item = query_one("SELECT * FROM gallery WHERE id = %s", (item_id,)) if item_id else None

    if request.method == "POST":
        label = (request.form.get("label") or "").strip()
        sort_order = int(request.form.get("sort_order") or 0)
        is_hero = 1 if request.form.get("is_hero") else 0
        image_url = item["image_url"] if item else None

        if request.files.get("image") and request.files["image"].filename:
            try:
                image_url = save_upload(request.files["image"], current_app.root_path)
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("admin/gallery_form.html", item=item)

        if not image_url and not item:
            flash("Please upload an image.", "error")
            return render_template("admin/gallery_form.html", item=item)

        if is_hero:
            execute("UPDATE gallery SET is_hero = 0")

        if item:
            execute(
                "UPDATE gallery SET label=%s, image_url=%s, sort_order=%s, is_hero=%s WHERE id=%s",
                (label, image_url, sort_order, is_hero, item_id),
            )
            flash("Photo updated.", "success")
        else:
            execute(
                "INSERT INTO gallery (label, image_url, sort_order, is_hero) VALUES (%s,%s,%s,%s)",
                (label, image_url, sort_order, is_hero),
            )
            flash("Photo added.", "success")
        return redirect(url_for("admin.gallery_list"))

    return render_template("admin/gallery_form.html", item=item)


@admin_bp.route("/gallery/<int:item_id>/delete", methods=["POST"])
@admin_required
def gallery_delete(item_id):
    execute("DELETE FROM gallery WHERE id = %s", (item_id,))
    flash("Photo deleted.", "success")
    return redirect(url_for("admin.gallery_list"))


# ---------- Contacts ----------
@admin_bp.route("/contacts")
@admin_required
def contacts_list():
    items = query_all("""SELECT c.*,
        (SELECT sc.id FROM site_chats sc JOIN site_users su ON su.id=sc.user_id
         WHERE su.email=c.email ORDER BY sc.id DESC LIMIT 1) AS chat_id
        FROM contacts c ORDER BY c.created_at DESC""")
    return render_template("admin/contacts_list.html", contacts=items)


@admin_bp.route("/contacts/<int:item_id>/delete", methods=["POST"])
@admin_required
def contact_delete(item_id):
    execute("DELETE FROM contacts WHERE id = %s", (item_id,))
    flash("Message deleted.", "success")
    return redirect(url_for("admin.contacts_list"))


# ---------- Research publications ----------
def safe_research_url(value):
    value = (value or "").strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password and "\\" not in value:
        return value
    return None


@admin_bp.route("/research")
@admin_required
def research_list():
    items = query_all("SELECT * FROM research_items ORDER BY sort_order ASC, published_on DESC, id DESC")
    return render_template("admin/research_list.html", items=items)


@admin_bp.route("/research/new", methods=["GET", "POST"])
@admin_bp.route("/research/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def research_form(item_id=None):
    item = query_one("SELECT * FROM research_items WHERE id=%s", (item_id,)) if item_id else None
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        authors = (request.form.get("authors") or "").strip()
        publication = (request.form.get("publication") or "").strip()
        pub_type = (request.form.get("publication_type") or "Journal article").strip()
        published_on = (request.form.get("published_on") or "").strip() or None
        abstract = (request.form.get("abstract") or "").strip()
        url_value = (request.form.get("url") or "").strip()
        doi = (request.form.get("doi") or "").strip()
        try:
            rank = int(request.form.get("sort_order") or 0)
        except ValueError:
            rank = -1
        if not title or len(title) > 240 or len(authors) > 500 or len(publication) > 240 or len(pub_type) > 80 or len(doi) > 255 or len(abstract) > 5000 or rank < 0:
            flash("Check the title, field lengths, and display order.", "error")
            return render_template("admin/research_form.html", item=item)
        elif published_on:
            try:
                datetime.strptime(published_on, "%Y-%m-%d")
            except ValueError:
                flash("Enter the publication date in YYYY-MM-DD format.", "error")
                return render_template("admin/research_form.html", item=item)
        url = safe_research_url(url_value) if url_value else None
        if url_value and not url:
            flash("Publication links must use a valid HTTPS address.", "error")
        else:
            payload = (title, authors or None, publication or None, pub_type or "Journal article", published_on, abstract or None, url, doi or None, rank, 1 if request.form.get("is_published") else 0)
            if item:
                execute("""UPDATE research_items SET title=%s,authors=%s,publication=%s,publication_type=%s,
                    published_on=%s,abstract=%s,url=%s,doi=%s,sort_order=%s,is_published=%s WHERE id=%s""", (*payload,item_id))
                flash("Research entry updated.", "success")
            else:
                execute("""INSERT INTO research_items (title,authors,publication,publication_type,published_on,abstract,url,doi,sort_order,is_published)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", payload)
                flash("Research entry added.", "success")
            return redirect(url_for("admin.research_list"))
    return render_template("admin/research_form.html", item=item)


@admin_bp.route("/research/<int:item_id>/delete", methods=["POST"])
@admin_required
def research_delete(item_id):
    execute("DELETE FROM research_items WHERE id=%s", (item_id,))
    flash("Research entry deleted.", "success")
    return redirect(url_for("admin.research_list"))


# ---------- Visitor chats ----------
@admin_bp.route("/chats")
@admin_required
def chats_list():
    items = query_all("""SELECT c.id,c.status,c.updated_at,u.name,u.email,
        (SELECT m.body FROM site_chat_messages m WHERE m.chat_id=c.id ORDER BY m.id DESC LIMIT 1) AS last_message,
        (SELECT COUNT(*) FROM site_chat_messages m WHERE m.chat_id=c.id AND m.sender_type='user') AS visitor_messages
        FROM site_chats c JOIN site_users u ON u.id=c.user_id ORDER BY c.updated_at DESC""")
    return render_template("admin/chats_list.html", chats=items)


@admin_bp.route("/chats/<int:chat_id>", methods=["GET", "POST"])
@admin_required
def chat_detail(chat_id):
    chat = query_one("SELECT c.*,u.name,u.email FROM site_chats c JOIN site_users u ON u.id=c.user_id WHERE c.id=%s", (chat_id,))
    if not chat:
        flash("Chat not found.", "error")
        return redirect(url_for("admin.chats_list"))
    if request.method == "POST":
        body = (request.form.get("message") or "").strip()
        if not body or len(body) > 2000:
            flash("Reply must be between 1 and 2,000 characters.", "error")
        else:
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO site_chat_messages (chat_id,sender_type,sender_id,body) VALUES (%s,'admin',%s,%s)", (chat_id,session.get("admin_id"),body))
                    cur.execute("UPDATE site_chats SET status='open',updated_at=CURRENT_TIMESTAMP WHERE id=%s", (chat_id,))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            flash("Reply sent.", "success")
            return redirect(url_for("admin.chat_detail", chat_id=chat_id))
    messages = query_all("SELECT * FROM site_chat_messages WHERE chat_id=%s ORDER BY id ASC", (chat_id,))
    return render_template("admin/chat_detail.html", chat=chat, messages=messages)


# ---------- Blog ----------
def make_slug(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug[:220] or "post"


@admin_bp.route("/blog")
@admin_required
def blog_list():
    posts = query_all("SELECT * FROM blog_posts ORDER BY updated_at DESC, id DESC")
    return render_template("admin/blog_list.html", posts=posts)


@admin_bp.route("/blog/new", methods=["GET", "POST"])
@admin_bp.route("/blog/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def blog_form(item_id=None):
    post = query_one("SELECT * FROM blog_posts WHERE id = %s", (item_id,)) if item_id else None
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        slug = make_slug(request.form.get("slug") or title)
        body = (request.form.get("body") or "").strip()
        status = "published" if request.form.get("status") == "published" else "draft"
        if not title or not body:
            flash("Title and article content are required.", "error")
            return render_template("admin/blog_form.html", post=post)
        collision = query_one("SELECT id FROM blog_posts WHERE slug = %s AND id <> %s", (slug, item_id or 0))
        if collision:
            slug = f"{slug}-{item_id or 'new'}"
        image = post.get("cover_image") if post else None
        if request.files.get("cover_image") and request.files["cover_image"].filename:
            try:
                image = save_upload(request.files["cover_image"], current_app.root_path)
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("admin/blog_form.html", post=post)
        published_at = post.get("published_at") if post else None
        if status == "published" and not published_at:
            published_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if status == "draft":
            published_at = None
        values = (
            title, slug, (request.form.get("excerpt") or "").strip(), body, image,
            (request.form.get("category") or "Technology").strip(),
            (request.form.get("tags") or "").strip(),
            (request.form.get("author") or "ENGSAQAWE").strip(), status,
            (request.form.get("seo_title") or "").strip() or None,
            (request.form.get("seo_description") or "").strip() or None,
            published_at,
        )
        if post:
            execute("""UPDATE blog_posts SET title=%s, slug=%s, excerpt=%s, body=%s, cover_image=%s,
                category=%s, tags=%s, author=%s, status=%s, seo_title=%s, seo_description=%s,
                published_at=%s WHERE id=%s""", (*values, item_id))
            flash("Article updated.", "success")
        else:
            execute("""INSERT INTO blog_posts
                (title, slug, excerpt, body, cover_image, category, tags, author, status, seo_title, seo_description, published_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", values)
            flash("Article created.", "success")
        return redirect(url_for("admin.blog_list"))
    return render_template("admin/blog_form.html", post=post)


@admin_bp.route("/blog/<int:item_id>/delete", methods=["POST"])
@admin_required
def blog_delete(item_id):
    execute("DELETE FROM blog_posts WHERE id = %s", (item_id,))
    flash("Article deleted.", "success")
    return redirect(url_for("admin.blog_list"))


@admin_bp.route("/blog/comments")
@admin_required
def blog_comments():
    comments = query_all("""SELECT bc.*, bp.title AS post_title, bp.slug AS post_slug
        FROM blog_comments bc JOIN blog_posts bp ON bp.id = bc.post_id
        ORDER BY CASE WHEN bc.status='pending' THEN 0 ELSE 1 END, bc.created_at DESC""")
    return render_template("admin/blog_comments.html", comments=comments)


@admin_bp.route("/blog/comments/<int:item_id>/<action>", methods=["POST"])
@admin_required
def blog_comment_action(item_id, action):
    if action == "approve":
        execute("UPDATE blog_comments SET status='approved' WHERE id=%s", (item_id,))
        flash("Comment approved.", "success")
    elif action == "delete":
        execute("DELETE FROM blog_comments WHERE id=%s", (item_id,))
        flash("Comment deleted.", "success")
    else:
        abort(404)
    return redirect(url_for("admin.blog_comments"))


# ---------- Footer links ----------
@admin_bp.route("/affiliates", methods=["GET", "POST"])
@admin_required
def affiliates_list():
    if request.method == "POST":
        label = (request.form.get("label") or "").strip()
        link = (request.form.get("url") or "").strip()
        description = (request.form.get("description") or "").strip()
        safe_link = safe_affiliate_destination(link)
        image_url = None
        if not label or len(label) > 120 or len(link) > 500 or len(description) > 500 or not safe_link:
            flash("Enter a name, a valid destination link, and a description up to 500 characters.", "error")
        else:
            if request.files.get("image") and request.files["image"].filename:
                try:
                    image_url = save_upload(request.files["image"], current_app.root_path)
                except ValueError as exc:
                    flash(str(exc), "error")
                    return redirect(url_for("admin.affiliates_list"))
            try:
                order = int(request.form.get("sort_order") or 0)
            except ValueError:
                order = 0
            execute(
                """INSERT INTO footer_links (section_title, label, url, image_url, description, sort_order, section_order, is_active)
                   VALUES ('Affiliate links', %s, %s, %s, %s, %s, 0, %s)""",
                (label, link, image_url, description or None, order, 1 if request.form.get("is_active") else 0),
            )
            flash("Affiliate link added.", "success")
            return redirect(url_for("admin.affiliates_list"))

    links = query_all(
        """SELECT * FROM footer_links WHERE LOWER(section_title) = 'affiliate links'
           ORDER BY sort_order, id"""
    )
    return render_template("admin/affiliates_list.html", links=links)


@admin_bp.route("/affiliates/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def affiliate_edit(item_id):
    item = query_one(
        """SELECT * FROM footer_links WHERE id = %s
           AND LOWER(section_title) = 'affiliate links'""",
        (item_id,),
    )
    if not item:
        flash("Affiliate link not found.", "error")
        return redirect(url_for("admin.affiliates_list"))

    if request.method == "POST":
        label = (request.form.get("label") or "").strip()
        link = (request.form.get("url") or "").strip()
        description = (request.form.get("description") or "").strip()
        safe_link = safe_affiliate_destination(link)
        image_url = None if request.form.get("remove_image") else item["image_url"]
        try:
            order = int(request.form.get("sort_order") or 0)
        except ValueError:
            order = 0
        if not label or len(label) > 120 or len(link) > 500 or len(description) > 500 or not safe_link:
            flash("Enter a name, a valid destination link, and a description up to 500 characters.", "error")
        else:
            if request.files.get("image") and request.files["image"].filename:
                try:
                    image_url = save_upload(request.files["image"], current_app.root_path)
                except ValueError as exc:
                    flash(str(exc), "error")
                    return render_template("admin/affiliate_form.html", item=item)
            execute(
                """UPDATE footer_links SET label=%s, url=%s, image_url=%s, description=%s, sort_order=%s, is_active=%s,
                   section_title='Affiliate links', section_order=0 WHERE id=%s""",
                (label, link, image_url, description or None, order, 1 if request.form.get("is_active") else 0, item_id),
            )
            flash("Affiliate link updated.", "success")
            return redirect(url_for("admin.affiliates_list"))
    return render_template("admin/affiliate_form.html", item=item)


@admin_bp.route("/affiliates/<int:item_id>/delete", methods=["POST"])
@admin_required
def affiliate_delete(item_id):
    execute(
        """DELETE FROM footer_links WHERE id=%s
           AND LOWER(section_title) = 'affiliate links'""",
        (item_id,),
    )
    flash("Affiliate link deleted.", "success")
    return redirect(url_for("admin.affiliates_list"))


@admin_bp.route("/footer-links", methods=["GET", "POST"])
@admin_required
def footer_links():
    if request.method == "POST":
        title = (request.form.get("section_title") or "").strip()
        label = (request.form.get("label") or "").strip()
        link = (request.form.get("url") or "").strip()
        safe_link = link.startswith(("/", "#", "https://", "http://", "mailto:", "tel:")) and not link.startswith("//") and "\\" not in link
        reserved_section = " ".join(title.casefold().split())
        if not title or len(title) > 120 or not label or len(label) > 120 or len(link) > 500 or not safe_link:
            flash("Section, label, and URL are required.", "error")
        elif reserved_section in {"affiliate links", "affiliates"}:
            flash("Manage affiliate links from the Affiliate Links section so they appear only once.", "error")
        elif reserved_section == "selected projects":
            flash("Selected project links come from your Projects list and are included in the footer automatically.", "error")
        else:
            try:
                order = int(request.form.get("sort_order") or 0)
                section_order = int(request.form.get("section_order") or 0)
            except ValueError:
                order = section_order = 0
            execute("""INSERT INTO footer_links (section_title, label, url, sort_order, section_order, is_active)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (title, label, link, order, section_order, 1 if request.form.get("is_active") else 0))
            flash("Footer link added.", "success")
            return redirect(url_for("admin.footer_links"))
    links = query_all("SELECT * FROM footer_links WHERE LOWER(TRIM(section_title)) NOT IN ('affiliate links','affiliates','selected projects') ORDER BY section_order, sort_order, id")
    selected_projects = query_all("SELECT id,title,live_link FROM projects ORDER BY sort_order,id LIMIT 5")
    return render_template("admin/footer_links.html", links=links, selected_projects=selected_projects)


@admin_bp.route("/footer-links/<int:item_id>/delete", methods=["POST"])
@admin_required
def footer_link_delete(item_id):
    execute("DELETE FROM footer_links WHERE id = %s AND LOWER(TRIM(section_title)) NOT IN ('affiliate links','affiliates','selected projects')", (item_id,))
    flash("Footer link deleted.", "success")
    return redirect(url_for("admin.footer_links"))


@admin_bp.route("/footer-links/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def footer_link_edit(item_id):
    item = query_one("SELECT * FROM footer_links WHERE id = %s AND LOWER(TRIM(section_title)) NOT IN ('affiliate links','affiliates','selected projects')", (item_id,))
    if not item:
        flash("Footer link not found.", "error")
        return redirect(url_for("admin.footer_links"))
    if request.method == "POST":
        title = (request.form.get("section_title") or "").strip()
        label = (request.form.get("label") or "").strip()
        link = (request.form.get("url") or "").strip()
        try:
            order = int(request.form.get("sort_order") or 0)
            section_order = int(request.form.get("section_order") or 0)
        except ValueError:
            order = section_order = 0
        safe_link = link.startswith(("/", "#", "https://", "http://", "mailto:", "tel:")) and not link.startswith("//") and "\\" not in link
        reserved_section = " ".join(title.casefold().split())
        if not title or not label or not safe_link:
            flash("Section, label, and URL are required.", "error")
        elif reserved_section in {"affiliate links", "affiliates"}:
            flash("Manage affiliate links from the Affiliate Links section so they appear only once.", "error")
        elif reserved_section == "selected projects":
            flash("Selected project links come from your Projects list and are included in the footer automatically.", "error")
        else:
            execute("""UPDATE footer_links SET section_title=%s, label=%s, url=%s,
                sort_order=%s, section_order=%s, is_active=%s WHERE id=%s""",
                (title, label, link, order, section_order, 1 if request.form.get("is_active") else 0, item_id))
            flash("Footer link updated.", "success")
            return redirect(url_for("admin.footer_links"))
    return render_template("admin/footer_link_form.html", item=item)
