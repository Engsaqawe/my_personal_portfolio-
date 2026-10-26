"""Reset an existing admin password from a local terminal, without echoing it."""

import getpass

from auth import hash_password
from database import get_db


def main():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username FROM admins WHERE is_active = 1 ORDER BY id"
            )
            admins = cur.fetchall()

        if not admins:
            print("No active admin accounts found.")
            return

        print("Active admin accounts:")
        for admin in admins:
            print(f"- {admin['username']}")

        username = input("Username to reset: ").strip()
        selected = next(
            (admin for admin in admins if admin["username"] == username), None
        )
        if selected is None:
            print("That username is not an active admin account.")
            return

        password = getpass.getpass("New password (12+ characters): ")
        confirmation = getpass.getpass("Confirm new password: ")
        if len(password) < 12:
            print("Password must be at least 12 characters long.")
            return
        if password != confirmation:
            print("The passwords did not match; no changes were made.")
            return

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE admins SET password_hash = %s WHERE id = %s",
                (hash_password(password), selected["id"]),
            )
        conn.commit()
        print(f"Password reset for {username}.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
