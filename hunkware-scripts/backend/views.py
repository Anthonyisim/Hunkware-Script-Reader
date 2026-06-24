import io

from flask import Blueprint, render_template, request, jsonify, session, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from parser import parse_work_order
from scripts_engine import generate_script, SCRIPT_TYPES

main_bp = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"pdf"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@main_bp.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user, script_types=SCRIPT_TYPES)


@main_bp.route("/api/upload", methods=["POST"])
@login_required
def upload_work_order():
    """
    Accepts a PDF work order, parses it in-memory (never written to disk),
    and returns the extracted fields as JSON for the review form to
    pre-fill. Nothing is persisted server-side from the PDF itself.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are accepted."}), 400

    filename = secure_filename(file.filename)

    try:
        file_bytes = file.read()
        stream = io.BytesIO(file_bytes)
        data = parse_work_order(stream)
    except Exception as e:
        return jsonify({"error": f"Could not read this PDF. ({str(e)[:200]})"}), 422

    missing = [k for k, v in data.items() if v in (None, "", []) and k != "items"]
    return jsonify({"fields": data, "missing_fields": missing, "source_filename": filename})


@main_bp.route("/api/generate", methods=["POST"])
@login_required
def generate():
    payload = request.get_json(silent=True) or {}

    script_type = payload.get("script_type")
    if script_type not in SCRIPT_TYPES:
        return jsonify({"error": "Unknown script type."}), 400

    job = payload.get("fields", {})
    caller_name = (payload.get("caller_name") or current_user.name or "[Name]").strip() or "[Name]"

    # Normalize items: front-end may send a newline/comma separated string
    items = job.get("items")
    if isinstance(items, str):
        job["items"] = [i.strip() for i in items.replace("\n", ",").split(",") if i.strip()]

    try:
        script_text = generate_script(script_type, job, caller_name=caller_name)
    except Exception as e:
        return jsonify({"error": f"Could not generate script. ({str(e)[:200]})"}), 422

    return jsonify({
        "script_type": script_type,
        "script_label": SCRIPT_TYPES[script_type],
        "script_text": script_text,
    })
