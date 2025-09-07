# db_ops.py (example)
from app import create_app
from src.extensions import db
from src.models import Task

app = create_app()
with app.app_context():
    print(Task.query.count())
    # db.create_all()   # or any other DB ops
