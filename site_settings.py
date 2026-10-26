"""Site-wide editable text/settings for ENGSAQAWE public pages."""

from db_helpers import query_all, query_one, execute

SETTING_GROUPS = [
    ("seo", "SEO & Site"),
    ("hero", "Hero"),
    ("skills", "What I Do"),
    ("about", "About"),
    ("services", "Services"),
    ("portfolio", "Portfolio"),
    ("affiliates", "Affiliates"),
    ("academy", "Academy"),
    ("certs", "Certificates"),
    ("contact", "Contact"),
    ("blog", "Blog"),
    ("footer", "Header & Footer"),
]

SETTINGS_SCHEMA = [
    ("meta_description", "seo", "Meta description", "ENGSAQAWE — websites, apps, and systems built by Nor Ali Saqawe.", "textarea"),
    ("site_url", "seo", "Site URL", "https://engsaqawe.com", "text"),
    ("job_title", "seo", "Job title (SEO)", "Software Engineer", "text"),
    ("og_image_path", "seo", "OG image path (under static/)", "images/pictures/me.png", "text"),
    ("typewriter_prefix", "hero", "Typewriter prefix", "I build ", "text"),
    ("typewriter_phrases", "hero", "Typewriter phrases (one per line)", "websites.\nweb apps.\nclean UI.\nMySQL systems.\ndigital tools.", "textarea"),
    ("hero_cta_primary", "hero", "Primary CTA button", "View Portfolio", "text"),
    ("hero_cta_secondary", "hero", "Secondary CTA button", "About Me", "text"),
    ("hero_eyebrow", "hero", "Hero eyebrow", "Developer · Builder · Educator", "text"),
    ("hero_badge", "hero", "Portrait badge text", "Open for work", "text"),
    ("stat_projects_label", "hero", "Stat 1 label", "Projects", "text"),
    ("stat_performance_label", "hero", "Stat 2 label", "Performance", "text"),
    ("stat_performance_value", "hero", "Stat 2 value", "95", "number"),
    ("stat_skills_label", "hero", "Stat 3 label", "Skills", "text"),
    ("stat_skills_value", "hero", "Stat 3 value", "6", "number"),
    ("skills_eyebrow", "skills", "Section eyebrow", "What I Do", "text"),
    ("skills_title", "skills", "Section title (use | before accent word)", "Things I|build", "text"),
    ("skills_subtitle", "skills", "Section subtitle", "Websites, apps, and tools for real clients.", "text"),
    ("skills_cards", "skills", "Skill cards (icon|title|text per line)", "fa-globe|Websites|Fast, clean sites with smooth animations.\nfa-cloud|Web Apps|Full apps with Flask, MySQL, and dashboards.\nfa-wand-magic-sparkles|UI & Motion|Animations, custom cursors, and clean design.\nfa-database|Systems|MySQL databases, APIs, and contact forms.\nfa-graduation-cap|Teaching|Courses and lessons for new developers.", "textarea"),
    ("about_eyebrow", "about", "Section eyebrow", "About", "text"),
    ("about_intro", "about", "Section introduction", "", "textarea"),
    ("about_title", "about", "Section title (use | before accent)", "About|Me", "text"),
    ("mission_label", "about", "Mission label", "Mission", "text"),
    ("vision_label", "about", "Vision label", "Vision", "text"),
    ("technologies_label", "about", "Technologies label", "Technologies", "text"),
    ("tech_list", "about", "Tech chips (comma-separated)", "Python,Flask,JavaScript,HTML5,CSS3,MySQL,UI/UX", "text"),
    ("timeline_items", "about", "Timeline (title|meta|body per line)", "Principal Frontend & Product Engineer|2021 — Present|Interface architecture, design systems, and performance budgets for products at scale.\nCreative Technology & Prototyping|2018 — 2021|Motion-driven storytelling and real-time experiences for brands and startups.", "textarea"),
    ("services_eyebrow", "services", "Services eyebrow", "Freelance services", "text"),
    ("services_title", "services", "Services title (use | before accent)", "I’m a freelancer — here’s|what I do", "text"),
    ("services_subtitle", "services", "Services subtitle", "Five ways I can help with your project. Pick one service or combine them, then tell me what you need.", "textarea"),
    ("services_cta_title", "services", "Services call-to-action", "Not sure which service fits?", "text"),
    ("services_cta_text", "services", "Services call-to-action details", "Tell me about your idea and we will work out the best next step.", "textarea"),
    ("services_cta_label", "services", "Services call-to-action button", "Let’s talk", "text"),
    ("portfolio_eyebrow", "portfolio", "Section eyebrow", "Portfolio", "text"),
    ("portfolio_title", "portfolio", "Section title (use | before accent)", "My|Projects", "text"),
    ("portfolio_subtitle", "portfolio", "Section subtitle", "Scroll down — projects move sideways with responsive device previews.", "text"),
    ("portfolio_filters", "portfolio", "Filters (value:Label comma-separated)", "all:All,saas:SaaS,enterprise:Enterprise,experiments:Experiments", "text"),
    ("portfolio_swipe_text", "portfolio", "Mobile swipe hint", "Swipe for more projects", "text"),
    ("portfolio_demo_label", "portfolio", "Live demo button", "Live Demo", "text"),
    ("portfolio_challenge_label", "portfolio", "Challenge label", "Challenge:", "text"),
    ("portfolio_solution_label", "portfolio", "Solution label", "Solution:", "text"),
    ("portfolio_source_label", "portfolio", "Source link label", "GitHub", "text"),
    ("portfolio_empty", "portfolio", "Empty projects message", "No projects yet.", "text"),
    ("academy_eyebrow", "academy", "Section eyebrow", "Academy", "text"),
    ("academy_title", "academy", "Section title (use | before accent)", "ENGSAQAWE|Academy", "text"),
    ("academy_subtitle", "academy", "Section subtitle", "Learn real skills for web development.", "text"),
    ("academy_progress_suffix", "academy", "Progress suffix", "% complete", "text"),
    ("academy_external_url", "academy", "External URL override (leave empty to use the Academy catalog)", "", "text"),
    ("academy_external_label", "academy", "Academy button label", "Browse courses", "text"),
    ("academy_empty", "academy", "Empty courses message", "New courses are coming soon.", "text"),
    ("certs_eyebrow", "certs", "Section eyebrow", "Certificates", "text"),
    ("certs_title", "certs", "Section title (use | before accent)", "My|Certificates", "text"),
    ("certs_subtitle", "certs", "Section subtitle", "Qualifications and awards.", "text"),
    ("certs_see_all", "certs", "See all button", "See all", "text"),
    ("certs_preview_label", "certs", "Preview link label", "Preview", "text"),
    ("certs_download_label", "certs", "Download link label", "Download", "text"),
    ("certs_modal_title", "certs", "Certificate modal title", "All Certificates", "text"),
    ("certs_modal_subtitle", "certs", "Certificate modal subtitle", "Qualifications and professional awards.", "text"),
    ("certs_rank_note", "certs", "Ranking note", "Rank 1 appears first; the first three are shown initially.", "text"),
    ("blog_eyebrow", "blog", "Section eyebrow", "Ideas & Notes", "text"),
    ("blog_title", "blog", "Section title", "From the|Journal", "text"),
    ("blog_subtitle", "blog", "Section subtitle", "Practical notes on technology, product design, and building for the web.", "text"),
    ("blog_read_more", "blog", "Read article label", "Read article", "text"),
    ("nav_blog", "footer", "Nav: Blog", "Blog", "text"),
    ("contact_select_placeholder", "contact", "Project type placeholder", "Select an option (optional)", "text"),
    ("contact_message_placeholder", "contact", "Message placeholder", "Tell me about your project…", "text"),
    ("contact_name_label", "contact", "Name field label", "Name", "text"),
    ("contact_name_placeholder", "contact", "Name placeholder", "Your name", "text"),
    ("contact_email_field_label", "contact", "Email field label", "Email", "text"),
    ("contact_email_placeholder", "contact", "Email placeholder", "you@company.com", "text"),
    ("contact_type_label", "contact", "Project type label", "Project type", "text"),
    ("contact_message_label", "contact", "Message field label", "Message", "text"),
    ("contact_char_limit_hint", "contact", "Message limit hint", "250 characters maximum", "text"),
    ("footer_admin_label", "footer", "Admin link label", "Admin login", "text"),
    ("footer_back_top", "footer", "Back to top label", "Back to top", "text"),
    ("footer_blog_all", "footer", "Blog list button label", "All articles", "text"),
    ("contact_eyebrow", "contact", "Section eyebrow", "Contact", "text"),
    ("contact_title", "contact", "Section title (use | before accent)", "Let's|Connect", "text"),
    ("contact_subtitle", "contact", "Section subtitle", "Have a project? Send me a message.", "text"),
    ("contact_hint", "contact", "Form hint under button", "Your message is saved to the database.", "text"),
    ("contact_submit", "contact", "Submit button", "Send message", "text"),
    ("contact_location_label", "contact", "Location card title", "Location", "text"),
    ("contact_email_label", "contact", "Email card title", "Email", "text"),
    ("contact_social_label", "contact", "Social card title", "Social", "text"),
    ("whatsapp_country_code", "contact", "WhatsApp country code", "252", "text"),
    ("whatsapp_prefill", "contact", "WhatsApp prefill message", "Hi ENGSAQAWE, I saw your portfolio.", "text"),
    ("project_type_options", "contact", "Project type options (one per line)", "Product / SaaS\nMarketing website\nInternal tool\nConsulting", "textarea"),
    ("footer_rights", "footer", "Copyright suffix", "All rights reserved.", "text"),
    ("footer_projects_heading", "footer", "Projects group heading", "Selected projects", "text"),
    ("loader_text", "footer", "Loader text", "Loading…", "text"),
    ("nav_home", "footer", "Nav: Home", "Home", "text"),
    ("nav_about", "footer", "Nav: About", "About", "text"),
    ("nav_portfolio", "footer", "Nav: Portfolio", "Portfolio", "text"),
    ("nav_services", "footer", "Nav: Services", "Services", "text"),
    ("nav_affiliates", "footer", "Nav: Affiliates", "Affiliates", "text"),
    ("nav_academy", "footer", "Nav: Academy", "Academy", "text"),
    ("nav_certs", "footer", "Nav: Certificates", "Certificates", "text"),
    ("nav_contact", "footer", "Nav: Contact", "Contact", "text"),
    ("affiliate_eyebrow", "affiliates", "Affiliate section eyebrow", "Affiliate links", "text"),
    ("affiliate_title", "affiliates", "Affiliate section title (use | before accent)", "Tools I|recommend", "text"),
    ("affiliate_subtitle", "affiliates", "Affiliate section subtitle", "Services and tools you may find useful for your own website or project.", "textarea"),
    ("affiliate_disclosure_title", "affiliates", "Affiliate disclosure heading", "Affiliate disclosure", "text"),
    ("affiliate_disclosure", "affiliates", "Affiliate disclosure text", "Some links may be affiliate links. I may receive a commission if you purchase through them.", "textarea"),
    ("affiliate_description", "affiliates", "Fallback card description", "A service worth exploring for your next project.", "text"),
    ("affiliate_button_label", "affiliates", "Affiliate button label", "Visit website", "text"),
    ("affiliate_tag_label", "affiliates", "Affiliate card tag", "Affiliate link", "text"),
]


def defaults_dict():
    return {key: default for key, _g, _l, default, _t in SETTINGS_SCHEMA}


def schema_by_group():
    groups = {g: [] for g, _ in SETTING_GROUPS}
    labels = dict(SETTING_GROUPS)
    for key, group, label, default, itype in SETTINGS_SCHEMA:
        groups.setdefault(group, []).append({
            "key": key,
            "label": label,
            "default": default,
            "type": itype,
            "group_label": labels.get(group, group),
        })
    return [(gid, labels.get(gid, gid), groups[gid]) for gid, _ in SETTING_GROUPS if groups.get(gid)]


def get_site_settings():
    data = defaults_dict()
    try:
        rows = query_all("SELECT setting_key, setting_value FROM site_settings")
    except Exception:
        return data
    for row in rows:
        key = row.get("setting_key")
        if key and row.get("setting_value") is not None:
            data[key] = row["setting_value"]
    return data


def save_site_settings(form):
    for key, group, _label, _default, _itype in SETTINGS_SCHEMA:
        if key not in form:
            continue
        value = (form.get(key) or "").strip()
        existing = query_one("SELECT setting_key FROM site_settings WHERE setting_key = %s", (key,))
        if existing:
            execute(
                "UPDATE site_settings SET setting_value=%s, setting_group=%s WHERE setting_key=%s",
                (value, group, key),
            )
        else:
            execute(
                "INSERT INTO site_settings (setting_key, setting_value, setting_group) VALUES (%s,%s,%s)",
                (key, value, group),
            )


def parse_pipe_lines(text, parts=3):
    rows = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        bits = [b.strip() for b in line.split("|")]
        while len(bits) < parts:
            bits.append("")
        rows.append(tuple(bits[:parts]))
    return rows


def parse_filters(text):
    items = []
    for chunk in (text or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" in chunk:
            value, label = chunk.split(":", 1)
        else:
            value = label = chunk
        items.append({"value": value.strip(), "label": label.strip()})
    return items


def split_title(text, fallback_left="", fallback_right=""):
    text = (text or "").strip()
    if "|" in text:
        left, right = text.split("|", 1)
        return left.strip(), right.strip()
    if fallback_left or fallback_right:
        return fallback_left, fallback_right
    return text, ""
