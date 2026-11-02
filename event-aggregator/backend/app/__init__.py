"""
Local Event Aggregator - Flask application factory.

Implements the architecture described in Chapter Three of the proposal:
  - P1 Collect Data   -> routes/events.py (submission) + scripts/scraper.py
  - P2 Process/Tag    -> models/event.py validation + utils/categorise.py
  - P3 Moderate        -> routes/admin.py
  - P4 Display/Filter  -> routes/events.py (GET /events)
  - P5 Notifications   -> models/notification.py + utils/notify.py
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_object="app.config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from app.routes.auth import auth_bp
    from app.routes.events import events_bp
    from app.routes.categories import categories_bp
    from app.routes.admin import admin_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    # Serve the compiled React interface (frontend/dist) from Flask itself, so
    # the whole system runs as one program: start.bat -> http://localhost:5000.
    # During development the Vite server (npm run dev) is used instead.
    dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
    if os.path.isdir(dist):
        from flask import abort, send_from_directory

        @app.get("/", defaults={"path": ""})
        @app.get("/<path:path>")
        def interface(path):
            if path.startswith("api/"):
                abort(404)
            if path and os.path.isfile(os.path.join(dist, path)):
                return send_from_directory(dist, path)
            return send_from_directory(dist, "index.html")  # client-side routes

    return app
