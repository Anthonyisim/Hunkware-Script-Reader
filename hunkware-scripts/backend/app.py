"""
HunkWare Script Reader — Flask application.

Small-team internal tool: secure login, upload a work order PDF,
review/edit the auto-extracted fields, and generate one of the
call scripts in clean readable English.

Security notes:
- Passwords hashed with werkzeug's PBKDF2 (no plaintext storage).
- Session cookies are HttpOnly, SameSite=Lax, and Secure in production.
- CSRF protection on all state-changing forms via Flask-WTF-style token.
- File uploads restricted to .pdf, size-capped, processed in memory only
  (not persisted to disk) unless the team enables job history.
- All routes except /login require an authenticated session.
- SECRET_KEY and admin bootstrap credentials are read from environment
  variables — never hardcoded. See .env.example.
"""

import os
import secrets
from datetime import datetime, timezone

from flask import Flask
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

from db import db, User


def create_app():
    app = Flask(__name__)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        # Generate one for local/dev convenience; production deployments
        # MUST set SECRET_KEY explicitly (see deploy docs) or sessions
        # will reset on every restart.
        secret_key = secrets.token_hex(32)
    app.config["SECRET_KEY"] = secret_key

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB upload cap

    # Cookie / session security
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
    app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 8  # 8 hour session

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from auth import auth_bp
    from views import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        _bootstrap_admin(app)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        # Basic CSP — adjust if you add external assets/CDNs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; img-src 'self' data:;"
        )
        return response

    return app


def _bootstrap_admin(app):
    """
    Create an initial admin user on first run, ONLY if ADMIN_EMAIL and
    ADMIN_PASSWORD are set in the environment and no users exist yet.
    This avoids ever shipping a hardcoded default password.

    Multiple worker processes (gunicorn --workers N) each call create_app()
    independently and can race to insert the same row. Guard with a
    try/except around the commit and roll back on conflict instead of
    crashing the worker.
    """
    if User.query.first() is not None:
        return

    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        app.logger.warning(
            "No users exist and ADMIN_EMAIL/ADMIN_PASSWORD are not set. "
            "Set them in your environment and restart to create the first "
            "team login. See .env.example."
        )
        return

    user = User(
        email=admin_email.lower().strip(),
        name="Admin",
        password_hash=generate_password_hash(admin_password),
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(user)
    try:
        db.session.commit()
        app.logger.info(f"Created initial admin user: {admin_email}")
    except IntegrityError:
        # Another worker process won the race and created it first — fine.
        db.session.rollback()


if __name__ == "__main__":
    app = create_app()
    debug_mode = os.environ.get("FLASK_ENV") != "production"
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=debug_mode)
