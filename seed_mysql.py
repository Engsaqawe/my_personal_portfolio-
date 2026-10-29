"""Create tables and seed ENGSAQAWE MySQL database."""

from database import get_db
from auth import hash_password, DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASS
from site_settings import SETTINGS_SCHEMA

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(180) NOT NULL,
    project_type VARCHAR(80) DEFAULT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS site_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(180) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS site_chats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY site_chat_user (user_id),
    INDEX site_chat_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS site_chat_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chat_id INT NOT NULL,
    sender_type VARCHAR(10) NOT NULL,
    sender_id INT DEFAULT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX site_chat_message_order (chat_id, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS visitor_registry (
    visitor_key CHAR(64) PRIMARY KEY,
    first_seen_at DATETIME NOT NULL,
    last_seen_at DATETIME NOT NULL,
    INDEX visitor_last_seen (last_seen_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS visitor_daily_visits (
    visitor_key CHAR(64) NOT NULL,
    visit_date DATE NOT NULL,
    first_visit_at DATETIME NOT NULL,
    PRIMARY KEY (visitor_key, visit_date),
    INDEX visitor_day (visit_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS research_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(240) NOT NULL,
    authors VARCHAR(500) DEFAULT NULL,
    publication VARCHAR(240) DEFAULT NULL,
    publication_type VARCHAR(80) DEFAULT 'Journal article',
    published_on DATE DEFAULT NULL,
    abstract TEXT,
    url VARCHAR(1000) DEFAULT NULL,
    doi VARCHAR(255) DEFAULT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_published TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX research_publication_order (is_published, sort_order, published_on)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    features TEXT,
    challenges TEXT,
    solutions TEXT,
    tech_stack VARCHAR(255) NOT NULL,
    category VARCHAR(80) NOT NULL,
    image_url VARCHAR(255) DEFAULT NULL,
    live_link VARCHAR(255) DEFAULT NULL,
    source_link VARCHAR(255) DEFAULT NULL,
    sort_order INT DEFAULT 0,
    featured TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(120) NOT NULL UNIQUE,
    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    icon_class VARCHAR(120) NOT NULL DEFAULT 'fa-solid fa-code',
    accent_color VARCHAR(7) NOT NULL DEFAULT '#0BA22E',
    tags TEXT,
    cta_label VARCHAR(120) NOT NULL DEFAULT 'Let’s talk',
    cta_url VARCHAR(500) NOT NULL DEFAULT '#contact',
    art_type VARCHAR(30) NOT NULL DEFAULT 'web',
    sort_order INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS certificates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    issuer VARCHAR(160) NOT NULL,
    year VARCHAR(10) NOT NULL,
    description TEXT,
    image_url VARCHAR(255) NOT NULL,
    preview_url VARCHAR(255) DEFAULT NULL,
    download_url VARCHAR(255) DEFAULT NULL,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS academy_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    description VARCHAR(500) DEFAULT NULL,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    modules VARCHAR(80) NOT NULL,
    progress INT DEFAULT 0,
    icon VARCHAR(60) DEFAULT 'fa-code',
    thumbnail_url VARCHAR(500) DEFAULT NULL,
    level VARCHAR(50) DEFAULT 'Beginner',
    language VARCHAR(50) DEFAULT 'English',
    status VARCHAR(20) NOT NULL DEFAULT 'published',
    category_id INT DEFAULT NULL,
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(8) NOT NULL DEFAULT 'USD',
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS academy_students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(180) NOT NULL,
    password_hash VARCHAR(255) DEFAULT NULL,
    course_id INT DEFAULT NULL,
    status VARCHAR(40) DEFAULT 'active',
    progress INT DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS academy_lessons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(180) NOT NULL,
    description TEXT,
    video_url VARCHAR(1000) NOT NULL,
    duration VARCHAR(40) DEFAULT NULL,
    sort_order INT DEFAULT 0,
    is_preview TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX academy_lesson_course_order (course_id, sort_order, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS academy_enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    progress INT DEFAULT 0,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY academy_student_course (student_id, course_id),
    INDEX academy_enrollment_course (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS academy_lesson_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    lesson_id INT NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY academy_student_lesson (student_id, lesson_id),
    INDEX academy_progress_lesson (lesson_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS academy_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(8) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'demo_paid',
    transaction_ref VARCHAR(80) NOT NULL,
    payment_type VARCHAR(20) NOT NULL DEFAULT 'demo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX academy_payment_student (student_id),
    INDEX academy_payment_course (course_id),
    UNIQUE KEY academy_payment_reference (transaction_ref)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS academy_course_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    is_saved TINYINT(1) NOT NULL DEFAULT 0,
    is_liked TINYINT(1) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY academy_student_course_action (student_id,course_id),
    INDEX academy_course_action_course (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS academy_cart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY academy_student_cart_course (student_id,course_id),
    INDEX academy_cart_course (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS profile (
    id INT PRIMARY KEY DEFAULT 1,
    full_name VARCHAR(120) NOT NULL,
    brand_name VARCHAR(80) NOT NULL,
    tagline VARCHAR(180) NOT NULL,
    hero_title VARCHAR(255) NOT NULL,
    hero_subtitle TEXT NOT NULL,
    mission TEXT NOT NULL,
    vision TEXT NOT NULL,
    location_note VARCHAR(180) DEFAULT NULL,
    email VARCHAR(180) NOT NULL,
    whatsapp VARCHAR(40) DEFAULT NULL,
    github_url VARCHAR(255) DEFAULT NULL,
    linkedin_url VARCHAR(255) DEFAULT NULL,
    twitter_url VARCHAR(255) DEFAULT NULL,
    facebook_url VARCHAR(255) DEFAULT NULL,
    youtube_url VARCHAR(255) DEFAULT NULL,
    hero_image VARCHAR(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) DEFAULT NULL,
    email VARCHAR(180) DEFAULT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS gallery (
    id INT AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(120) DEFAULT NULL,
    image_url VARCHAR(255) NOT NULL,
    sort_order INT DEFAULT 0,
    is_hero TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS site_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT,
    setting_group VARCHAR(60) DEFAULT 'general',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blog_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(220) NOT NULL UNIQUE,
    excerpt VARCHAR(500) DEFAULT NULL,
    body MEDIUMTEXT NOT NULL,
    cover_image VARCHAR(255) DEFAULT NULL,
    category VARCHAR(100) DEFAULT NULL,
    tags VARCHAR(255) DEFAULT NULL,
    author VARCHAR(120) DEFAULT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    seo_title VARCHAR(200) DEFAULT NULL,
    seo_description VARCHAR(320) DEFAULT NULL,
    published_at DATETIME DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (status, published_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blog_post_views (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    visitor_key CHAR(64) NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_post_visitor (post_id, visitor_key),
    CONSTRAINT fk_blog_view_post FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blog_post_reactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    visitor_key CHAR(64) NOT NULL,
    reaction VARCHAR(12) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_post_reaction (post_id, visitor_key),
    CONSTRAINT fk_blog_reaction_post FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blog_comments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    name VARCHAR(80) NOT NULL,
    body VARCHAR(1200) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX blog_comments_status (status, created_at),
    CONSTRAINT fk_blog_comment_post FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS footer_links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    section_title VARCHAR(100) NOT NULL,
    label VARCHAR(120) NOT NULL,
    url VARCHAR(500) NOT NULL,
    image_url VARCHAR(500) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    sort_order INT DEFAULT 0,
    section_order INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

CERTIFICATES = [
    (
        "Certificate of Achievement",
        "Weblake Corp",
        "2025",
        "Recognized for exceptional effort, dedication, and accomplishment in professional development.",
        "images/pictures/certi1.jpg",
        "https://new.express.adobe.com/id/urn:aaid:sc:EU:3b5bf125-d435-5612-a1fb-934599f172d3",
        "images/pictures/certi1.jpg",
        1,
    ),
    (
        "Advanced Frontend Architecture",
        "International Tech Institute",
        "2025",
        "Scalable front-end architecture, design systems, performance, and accessibility for modern web apps.",
        "images/pictures/certi1.jpg",
        None,
        "images/pictures/certi1.jpg",
        2,
    ),
    (
        "Cloud-Native Systems",
        "Cloud Engineering Institute",
        "2024",
        "Distributed systems, reliability engineering, observability, and deployment strategies.",
        "images/pictures/certi1.jpg",
        None,
        "images/pictures/certi1.jpg",
        3,
    ),
]

COURSES = [
    (
        "Interface Systems Lab",
        "Build a production-ready design system from tokens to motion using native web technologies.",
        "6 modules",
        72,
        "fa-bezier-curve",
        1,
    ),
    (
        "Performance By Design",
        "Design and engineer for Lighthouse 95+ without sacrificing visuals, motion, or ambition.",
        "4 modules",
        54,
        "fa-gauge-high",
        2,
    ),
    (
        "Motion for Product Teams",
        "Practical motion design in product interfaces — principles to implementation in CSS and JS.",
        "5 modules",
        38,
        "fa-wave-square",
        3,
    ),
]

PROFILE = (
    "Nor Ali Saqawe",
    "ENGSAQAWE",
    "Developer · Builder · Educator",
    "Engineering quiet breakthroughs for loud results.",
    "I craft scalable systems, premium web applications, and digital experiences that feel effortless on the surface and powerful underneath.",
    "To build software that feels inevitable — interfaces and systems so considered they get out of the way and let teams do their best work.",
    "A world where ambitious ideas are not constrained by tooling. ENGSAQAWE turns complex requirements into precise, calm, scalable digital products.",
    "Remote-friendly · Available worldwide",
    "nuurc9399@gmail.com",
    "684421687",
    "https://github.com",
    "https://www.linkedin.com",
    "https://x.com",
)


def run_sql(conn, sql):
    with conn.cursor() as cur:
        for statement in sql.strip().split(";"):
            stmt = statement.strip()
            if stmt:
                cur.execute(stmt)
    conn.commit()


GALLERY = [
    ("Hero portrait", "images/pictures/me.png", 1, 1),
    ("Portrait 2", "images/pictures/me2.png", 2, 0),
    ("Portrait 3", "images/pictures/me3.png", 3, 0),
    ("Portrait 4", "images/pictures/me4.png", 4, 0),
    ("Portrait 5", "images/pictures/5.png", 5, 0),
]

DEFAULT_SERVICES = [
    ("web-development", "Web Development", "Clean, fast, mobile-friendly websites for businesses, brands, and personal projects.", "fa-solid fa-code", "#0BA22E", "HTML & CSS\nJavaScript\nResponsive design", "Start a web project", "#contact", "web", 1, 1),
    ("full-stack-systems", "Full-Stack System Development", "Complete web systems with a front end, back end, and database, built around how you work.", "fa-solid fa-layer-group", "#1FA8A0", "Python\nFlask & Django\nDatabases", "Plan my system", "#contact", "stack", 2, 1),
    ("translation-transcription", "Somali–English Translation & Transcription", "Clear translation between Somali and English, and written transcripts of audio or video.", "fa-solid fa-language", "#E85D4C", "Somali ⇄ English\nTranscription\nDocuments", "Request a translation", "#contact", "lang", 3, 1),
    ("affiliate-marketing", "Affiliate Marketing & Online Promotion", "Helping products and services get seen online through honest content and affiliate links.", "fa-solid fa-bullhorn", "#4FB800", "Affiliate links\nOnline promotion\nContent", "Promote with me", "#contact", "net", 4, 1),
    ("online-teaching", "Online Teaching & Tutoring", "Patient, step-by-step lessons online, explained in simple words so learners can follow.", "fa-solid fa-chalkboard-user", "#0D7A22", "Online lessons\nOne-to-one help\nStep by step", "Book a lesson", "#contact", "learn", 5, 1),
]


def migrate_profile_columns(conn):
    columns = [
        ("facebook_url", "VARCHAR(255) DEFAULT NULL"),
        ("youtube_url", "VARCHAR(255) DEFAULT NULL"),
        ("hero_image", "VARCHAR(255) DEFAULT NULL"),
    ]
    with conn.cursor() as cur:
        for name, definition in columns:
            try:
                cur.execute(f"ALTER TABLE profile ADD COLUMN {name} {definition}")
            except Exception:
                pass
    conn.commit()


def seed():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES LIKE 'services'")
            services_table_exists = bool(cur.fetchone())
        run_sql(conn, SCHEMA)
        migrate_profile_columns(conn)

        with conn.cursor() as cur:
            migrations = {
                "courses": [
                    ("thumbnail_url", "VARCHAR(500) DEFAULT NULL"),
                    ("level", "VARCHAR(50) DEFAULT 'Beginner'"),
                    ("language", "VARCHAR(50) DEFAULT 'English'"),
                    ("status", "VARCHAR(20) NOT NULL DEFAULT 'published'"),
                    ("category_id", "INT DEFAULT NULL"),
                    ("price", "DECIMAL(10,2) NOT NULL DEFAULT 0.00"),
                    ("currency", "VARCHAR(8) NOT NULL DEFAULT 'USD'"),
                ],
                "academy_students": [("password_hash", "VARCHAR(255) DEFAULT NULL")],
            }
            for table, columns in migrations.items():
                for name, definition in columns:
                    cur.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (name,))
                    if not cur.fetchone():
                        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{name}` {definition}")

            if not services_table_exists:
                cur.executemany(
                    """INSERT INTO services
                       (slug, title, description, icon_class, accent_color, tags, cta_label, cta_url, art_type, sort_order, is_active)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    DEFAULT_SERVICES,
                )

            cur.execute("SHOW COLUMNS FROM footer_links LIKE 'image_url'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE footer_links ADD COLUMN image_url VARCHAR(500) DEFAULT NULL AFTER url")
            cur.execute("SHOW COLUMNS FROM footer_links LIKE 'description'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE footer_links ADD COLUMN description TEXT DEFAULT NULL AFTER image_url")
            cur.execute(
                """UPDATE footer_links SET description=%s
                   WHERE LOWER(section_title)='affiliate links' AND label='Namecheap Hosting'
                   AND (description IS NULL OR description='')""",
                ("Domain names and web hosting for your website.",),
            )

            cur.execute("SELECT COUNT(*) AS c FROM certificates")
            if cur.fetchone()["c"] == 0:
                cur.executemany(
                    """INSERT INTO certificates
                    (title, issuer, year, description, image_url, preview_url, download_url, sort_order)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    CERTIFICATES,
                )

            cur.execute("SELECT COUNT(*) AS c FROM courses")
            if cur.fetchone()["c"] == 0:
                cur.executemany(
                    """INSERT INTO courses (title, description, modules, progress, icon, sort_order)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                    COURSES,
                )

            cur.execute("SELECT COUNT(*) AS c FROM profile")
            if cur.fetchone()["c"] == 0:
                cur.execute(
                    """INSERT INTO profile
                    (id, full_name, brand_name, tagline, hero_title, hero_subtitle, mission, vision,
                     location_note, email, whatsapp, github_url, linkedin_url, twitter_url)
                    VALUES (1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    PROFILE,
                )

            # Update only the previous public default; preserve a custom email set by the owner.
            cur.execute("UPDATE profile SET email=%s WHERE id=1 AND email=%s", ("nuurc9399@gmail.com", "hello@engsaqawe.com"))
            cur.execute("UPDATE site_settings SET setting_value='' WHERE setting_key='contact_hint' AND setting_value=%s", ("Your message is saved to the database.",))
            cur.execute("UPDATE footer_links SET section_title='Affiliate links', section_order=0 WHERE LOWER(TRIM(section_title)) IN ('affiliate links','affiliates')")

            cur.execute("SELECT COUNT(*) AS c FROM admins")
            if cur.fetchone()["c"] == 0:
                if not DEFAULT_ADMIN_USER or not DEFAULT_ADMIN_PASS:
                    raise RuntimeError("Set ADMIN_USERNAME and ADMIN_PASSWORD before creating the first administrator.")
                cur.execute(
                    """INSERT INTO admins (username, password_hash, full_name, email)
                       VALUES (%s, %s, %s, %s)""",
                    (DEFAULT_ADMIN_USER, hash_password(DEFAULT_ADMIN_PASS), "Nor Ali Saqawe", "hello@engsaqawe.com"),
                )

            cur.execute("SELECT COUNT(*) AS c FROM gallery")
            if cur.fetchone()["c"] == 0:
                cur.executemany(
                    """INSERT INTO gallery (label, image_url, sort_order, is_hero)
                       VALUES (%s, %s, %s, %s)""",
                    GALLERY,
                )

            cur.execute("SELECT COUNT(*) AS c FROM footer_links WHERE LOWER(section_title) = 'affiliate links'")
            if cur.fetchone()["c"] == 0:
                cur.execute(
                    """INSERT INTO footer_links (section_title, label, url, sort_order, section_order, is_active)
                       VALUES ('Affiliate links', %s, %s, 0, 0, 1)""",
                    ("Namecheap Hosting", "https://www.namecheap.com/hosting/"),
                )

            # Seed any missing site_settings keys (never overwrite existing)
            for key, group, _label, default, _itype in SETTINGS_SCHEMA:
                cur.execute("SELECT setting_key FROM site_settings WHERE setting_key = %s", (key,))
                if not cur.fetchone():
                    cur.execute(
                        """INSERT INTO site_settings (setting_key, setting_value, setting_group)
                           VALUES (%s, %s, %s)""",
                        (key, default, group),
                    )

            cur.execute(
                """UPDATE site_settings SET setting_value=%s, setting_group='affiliates'
                   WHERE setting_key='affiliate_title' AND setting_value='Tools I Recommend'""",
                ("Tools I|recommend",),
            )

            # Prefer built-in Academy Panel over old external default
            cur.execute(
                """UPDATE site_settings SET setting_value=%s
                   WHERE setting_key='academy_external_url'
                   AND (setting_value=%s OR setting_value=%s)""",
                ("", "https://academy.engsaqawe.app", "https://academy.engsaqawe.app/"),
            )
            cur.execute(
                """UPDATE site_settings SET setting_value=%s
                   WHERE setting_key='academy_external_label' AND setting_value='Open Academy Panel'""",
                ("Browse courses",),
            )

        conn.commit()
        print("MySQL schema ready and seeded.")
    finally:
        conn.close()


def update_whatsapp():
    """Ensure profile WhatsApp matches site default."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE profile SET whatsapp = %s WHERE id = 1", ("684421687",))
        conn.commit()
        print("WhatsApp number updated.")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
    update_whatsapp()
