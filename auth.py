"""Admin authentication helpers."""

import os
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session, redirect, url_for, flash, request
from db_helpers import query_one


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in to continue.", "error")
            nxt = request.path or "/"
            return redirect(url_for("admin.login", next=nxt))
        return view(*args, **kwargs)

    return wrapped


def site_user_required(view):
    """Require a registered portfolio account for contact and chat actions."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("site_user_id"):
            flash("Sign in or create an account before sending a message.", "error")
            return redirect(url_for("account_login", next=request.full_path.rstrip("?") or "/#contact"))
        return view(*args, **kwargs)

    return wrapped


def login_admin(username, password):
    admin = query_one("SELECT * FROM admins WHERE username = %s AND is_active = 1", (username,))
    if not admin or not check_password_hash(admin["password_hash"], password):
        return None
    return admin


def get_admin_by_id(admin_id):
    return query_one("SELECT id, username, full_name, email FROM admins WHERE id = %s", (admin_id,))


def hash_password(password):
    return generate_password_hash(password)


DEFAULT_ADMIN_USER = os.getenv("ADMIN_USERNAME")
DEFAULT_ADMIN_PASS = os.getenv("ADMIN_PASSWORD")
