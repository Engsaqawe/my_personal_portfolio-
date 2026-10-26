"""Secure file upload helpers."""

import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join("static", "images", "pictures")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
IMAGE_SIGNATURES = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "gif": (b"GIF87a", b"GIF89a"),
    "webp": (b"RIFF",),
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, upload_root):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed. Use PNG, JPG, WEBP, or GIF.")

    ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
    header = file.stream.read(12)
    file.stream.seek(0)
    if not any(header.startswith(signature) for signature in IMAGE_SIGNATURES[ext]):
        raise ValueError("The uploaded file does not match its image type.")
    if ext == "webp" and (len(header) < 12 or header[8:12] != b"WEBP"):
        raise ValueError("The uploaded file does not match its image type.")
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    folder = os.path.join(upload_root, UPLOAD_FOLDER)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    file.save(path)
    return f"images/pictures/{filename}"
