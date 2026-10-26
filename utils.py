"""Shared helpers for ENGSAQAWE templates."""

TECH_ICONS = {
    "python": {"icon": "fa-brands fa-python", "class": "tech--python", "label": "Python"},
    "flask": {"icon": "fa-solid fa-server", "class": "tech--flask", "label": "Flask"},
    "javascript": {"icon": "fa-brands fa-js", "class": "tech--js", "label": "JavaScript"},
    "js": {"icon": "fa-brands fa-js", "class": "tech--js", "label": "JavaScript"},
    "html5": {"icon": "fa-brands fa-html5", "class": "tech--html", "label": "HTML5"},
    "html": {"icon": "fa-brands fa-html5", "class": "tech--html", "label": "HTML5"},
    "css3": {"icon": "fa-brands fa-css3-alt", "class": "tech--css", "label": "CSS3"},
    "css": {"icon": "fa-brands fa-css3-alt", "class": "tech--css", "label": "CSS3"},
    "mysql": {"icon": "fa-solid fa-database", "class": "tech--mysql", "label": "MySQL"},
    "redis": {"icon": "fa-solid fa-memory", "class": "tech--redis", "label": "Redis"},
    "docker": {"icon": "fa-brands fa-docker", "class": "tech--docker", "label": "Docker"},
    "gsap": {"icon": "fa-solid fa-film", "class": "tech--gsap", "label": "GSAP"},
    "lenis": {"icon": "fa-solid fa-arrows-up-down", "class": "tech--lenis", "label": "Lenis"},
    "ui/ux": {"icon": "fa-solid fa-palette", "class": "tech--ui", "label": "UI/UX"},
    "ui": {"icon": "fa-solid fa-palette", "class": "tech--ui", "label": "UI/UX"},
    "design systems": {"icon": "fa-solid fa-bezier-curve", "class": "tech--ui", "label": "Design Systems"},
    "accessibility": {"icon": "fa-solid fa-universal-access", "class": "tech--ui", "label": "Accessibility"},
    "animations": {"icon": "fa-solid fa-wand-magic-sparkles", "class": "tech--gsap", "label": "Animations"},
    "webgl": {"icon": "fa-solid fa-cube", "class": "tech--js", "label": "WebGL"},
    "interactions": {"icon": "fa-solid fa-hand-pointer", "class": "tech--js", "label": "Interactions"},
    "storytelling": {"icon": "fa-solid fa-book-open", "class": "tech--ui", "label": "Storytelling"},
}


def tech_meta(name):
    key = (name or "").strip().lower()
    return TECH_ICONS.get(key, {
        "icon": "fa-solid fa-code",
        "class": "tech--default",
        "label": name.strip(),
    })


def demo_link(project):
    link = (project.get("live_link") if isinstance(project, dict) else getattr(project, "live_link", None)) or ""
    if link and link != "#":
        return link
    title = project.get("title") if isinstance(project, dict) else project["title"]
    slug = title.lower().replace(" ", "-").replace("&", "and")
    return f"https://demo.engsaqawe.com/{slug}"


def cert_preview_href(cert):
    preview = (cert.get("preview_url") if isinstance(cert, dict) else cert.preview_url) or ""
    preview = preview.strip()
    if preview.startswith("http://") or preview.startswith("https://"):
        return preview
    from flask import url_for

    static_path = preview or (cert.get("image_url") if isinstance(cert, dict) else cert.image_url)
    return url_for("static", filename=static_path)


def cert_download_href(cert):
    from flask import url_for

    download = (cert.get("download_url") if isinstance(cert, dict) else cert.download_url) or ""
    download = download.strip()
    if download.startswith("http://") or download.startswith("https://"):
        return download
    static_path = download or (cert.get("image_url") if isinstance(cert, dict) else cert.image_url)
    return url_for("static", filename=static_path)
