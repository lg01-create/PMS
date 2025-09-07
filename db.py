# init_db.py
from app import create_app
from src.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    print("Database initialized at:", app.config["SQLALCHEMY_DATABASE_URI"])
