# Backend and Database Security Review

## Summary

The Flask app had several security weaknesses in authentication configuration, request forgery protection, uploads, and redirects. Code changes below address those issues. A live MySQL review could not be completed: the configured MySQL server rejected the connection because this environment has no `DB_PASSWORD` value. The local `database.db` file is a separate, older SQLite database and is not the database used by the current app.

## High severity

### SEC-01 — Secrets and bootstrap credentials were embedded in source

- **Severity:** High
- **Location:** `database.py:10`, `auth.py:39-40`, `app.py:24-26`, `seed_mysql.py:392-397`
- **Evidence:** Database and administrator values are now read from environment variables. Production startup now requires `SECRET_KEY`; first-admin seeding requires explicit `ADMIN_USERNAME` and `ADMIN_PASSWORD` values.
- **Impact:** Default or committed credentials can let an attacker access the database, administrator account, or forge Flask session cookies.
- **Fix applied:** Removed source-code fallback credentials and made production configuration fail closed when `SECRET_KEY` or `DB_PASSWORD` is absent.
- **Artifact cleanup:** Refreshed `__pycache__.zip` from current source files, added the new Projects/Affiliate assets, removed cached bytecode, and verified the archive no longer contains the previous fallback credential strings.
- **Follow-up:** Rotate the database, administrator, and session-signing secrets previously used with this project. Set `DB_PASSWORD` and `SECRET_KEY`; set `ADMIN_USERNAME` and `ADMIN_PASSWORD` only when bootstrapping a database without an admin.

### SEC-02 — State-changing requests lacked consistent CSRF protection

- **Severity:** High
- **Location:** `app.py:44-56`; POST forms throughout `templates/`
- **Evidence:** The app now validates a session-bound token on every POST/PUT/PATCH/DELETE request. All 33 POST forms include the token; blog reactions continue to use the existing session token.
- **Impact:** Without CSRF protection, a site an administrator visits could submit actions using their authenticated session.
- **Fix applied:** Added global token enforcement and form fields; changed both logout actions to POST.

### SEC-03 — Upload validation trusted file extensions and allowed SVG

- **Severity:** High
- **Location:** `uploads.py:8-35`
- **Evidence:** Uploads now allow only PNG, JPEG, GIF, and WebP extensions and verify the file signature; SVG is rejected. The app’s existing 8 MB request limit remains in force.
- **Impact:** An attacker could upload active SVG content or a non-image file with an image extension and serve it from the site.
- **Fix applied:** Added raster image allowlisting and basic content-signature validation.
- **Remaining limitation:** Signature checks do not fully decode images or scan them for malware.

## Medium severity

### SEC-04 — Admin login accepted an untrusted redirect target

- **Severity:** Medium
- **Location:** `admin_routes.py:27-46`
- **Evidence:** The post-login destination is now restricted to a local absolute path; protocol-relative URLs and backslashes are rejected. Login clears the existing session before setting the administrator identity.
- **Impact:** A crafted login link could redirect an administrator to an attacker-controlled site or retain pre-login session state.
- **Fix applied:** Added local-path validation and session renewal on successful login.

### SEC-05 — Cookie and development-server settings were unsafe as production defaults

- **Severity:** Medium
- **Location:** `app.py:20-34`, `app.py:296`; `academy_routes.py:10-30`
- **Evidence:** Sessions now use HttpOnly and SameSite=Lax cookies, Secure cookies in production, and an eight-hour maximum lifetime. Debug is disabled in production, and the built-in development server binds to localhost. Academy login also renews the session.
- **Impact:** Weak session settings or an exposed debug server can compromise administrator sessions or application execution.
- **Fix applied:** Added environment-aware secure settings and session renewal.

## Low severity / deployment checks

- Login attempts are not rate-limited. Add a shared rate limiter before exposing the admin login publicly.
- A Content Security Policy and Flask `TRUSTED_HOSTS` setting are not configured in the app. Confirm the production domain and required font/icon/CDN sources before setting these, and verify host restrictions at the edge if used there.
- Production WSGI server and TLS configuration are outside this code workspace; verify the deployed service uses HTTPS and a production WSGI server.

## Database review status

- Read-only MySQL connection attempt: **not available** because `DB_PASSWORD` is not set in this environment; the server returned an authentication rejection. Table contents, access grants, and whether the new `footer_links.image_url` migration has run remain unverified.
- Local `database.db` and its obsolete SQLite seeder: **removed at the user's request**, including database copies from `__pycache__.zip`. Before removal, the database was confirmed to be an older SQLite file with only `contacts` and `projects` tables (0 contacts and 4 projects). The active app uses MySQL.
- The `footer_links.image_url` column is included in the schema and an idempotent startup migration was added in `seed_mysql.py:350-353`. It must be verified against the configured MySQL database after credentials are set.

## Checks run

- Python modules compile successfully.
- JavaScript syntax checks pass for the Projects scripts.
- All Jinja templates parse successfully.
- CSRF tests confirm missing tokens are rejected, valid tokens allow logout, and GET logout is no longer accepted.
- Affiliate thumbnail URL validation accepts HTTPS/local static URLs and rejects `javascript:` URLs.
- Upload smoke check rejects SVG-like content renamed with a `.jpg` extension.
- SQL audit found no request-driven dynamic SQL; the sole SQL f-string assembles a migration statement from fixed internal column definitions. No Jinja `|safe` filters were found.
- The refreshed project archive was scanned and no previous fallback credential strings were found.
