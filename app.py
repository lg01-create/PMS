import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.extensions import db
from src.models import User, Event, Task, Contact, Note, Tag, TaskNote, TaskLink, Subtask, Bookmark, GmailAccount, OutlookAccount
from src.routes.auth import auth_bp, init_login_manager
from src.routes.dashboard import dashboard_bp
from src.routes.contacts import contacts_bp
from src.routes.notes import notes_bp
from src.routes.tasks import tasks_bp
from src.routes.calendar import calendar_bp
from src.routes.bookmarks import bookmarks_bp
from src.routes.email import email_bp

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    @app.context_processor
    def inject_current_app():
        # makes `current_app` and `config` available in all templates
        return {"current_app": app, "config": app.config}

    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    (DATA_DIR / "files").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "gmail" / "tokens").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "outlook" / "tokens").mkdir(parents=True, exist_ok=True)

    def to_abs_sqlite(uri_or_empty: str) -> str:
        if not uri_or_empty:
            return f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"
        if not uri_or_empty.lower().startswith("sqlite:"):
            return uri_or_empty
        parsed = urlparse(uri_or_empty)
        if uri_or_empty.startswith("sqlite:///C:") or uri_or_empty.startswith("sqlite:///D:"):
            return uri_or_empty
        if uri_or_empty.startswith("sqlite:///"):
            return f"sqlite:///{(BASE_DIR / parsed.path.lstrip('/')).as_posix()}"
        return f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
    env_db = os.getenv('DATABASE_URL', '').strip()
    app.config['SQLALCHEMY_DATABASE_URI'] = to_abs_sqlite(env_db)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TIMEZONE'] = os.getenv('TIMEZONE', 'America/Chicago')
    app.config['SCHEDULER_ENABLED'] = os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'true'
    app.config['GOOGLE_CLIENT_SECRETS'] = str(DATA_DIR / "gmail" / "client_secret.json")
    app.config['GOOGLE_TOKEN_DIR'] = str(DATA_DIR / "gmail" / "tokens")
    app.config['OUTLOOK_APP_CONFIG'] = str(DATA_DIR / "outlook" / "app_config.json")
    app.config['OUTLOOK_TOKEN_DIR'] = str(DATA_DIR / "outlook" / "tokens")
    app.config['EMAIL_LOOKBACK_DAYS'] = int(os.getenv('EMAIL_LOOKBACK_DAYS', '5'))

    print("=== PMS Startup ===")
    print("DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    print("Data dir:", DATA_DIR)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(contacts_bp, url_prefix="/contacts")
    app.register_blueprint(notes_bp, url_prefix="/notes")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(calendar_bp, url_prefix="/calendar")
    app.register_blueprint(bookmarks_bp, url_prefix="/bookmarks")
    app.register_blueprint(email_bp, url_prefix="/email")

    # Login
    login_manager = LoginManager()
    init_login_manager(login_manager, app)

    # Background scheduler (guard against debugger double-run)
    if app.config['SCHEDULER_ENABLED']:
        is_main = os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug
        if is_main:
            scheduler = BackgroundScheduler(
                daemon=True,
                timezone=app.config.get('TIMEZONE', 'America/Chicago')
            )
            scheduler.add_job(
                func=check_due_items,
                args=[app],
                trigger=IntervalTrigger(minutes=1),
                id='check_due_items',
                replace_existing=True,
                coalesce=True,
                max_instances=1
            )
            scheduler.start()
            import atexit
            atexit.register(lambda: scheduler.shutdown(wait=False))

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    return app

def check_due_items(app):
    from datetime import datetime, timedelta
    from src.models import Task, Event
    try:
        with app.app_context():
            now = datetime.now()
            soon = now + timedelta(minutes=5)
            due_tasks = Task.query.filter(Task.due_at != None, Task.due_at <= soon, Task.status != 'done').all()
            due_events = Event.query.filter(Event.start_at != None, Event.start_at <= soon).all()
            for t in due_tasks:
                print(f"[REMINDER] Task due soon: {t.title} @ {t.due_at}")
            for e in due_events:
                print(f"[REMINDER] Event starting soon: {e.title} @ {e.start_at}")
    except Exception as ex:
        import traceback
        print("[Scheduler] check_due_items failed:", ex)
        traceback.print_exc()

if __name__ == "__main__":
    app = create_app()

    cert = Path("certs/127.0.0.1+2.pem")
    key  = Path("certs/127.0.0.1+2-key.pem")
    if cert.exists() and key.exists():
        app.run(debug=True, ssl_context=(str(cert), str(key)))
    else:
        print("[HTTPS] Certs not found, running HTTP on http://127.0.0.1:5000")
        app.run(debug=True)
