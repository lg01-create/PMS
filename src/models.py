from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .extensions import db

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class User(UserMixin, db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=True)

class Contact(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

class Note(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=True)

# Tagging
task_tags = Table(
    'task_tags', db.metadata,
    Column('task_id', Integer, ForeignKey('task.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True)
)

class Tag(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

class Task(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='todo')  # todo, doing, done
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(20), default='other')  # work, personal, other

    notes = relationship('TaskNote', backref='task', cascade='all, delete-orphan')
    links = relationship('TaskLink', backref='task', cascade='all, delete-orphan')
    subtasks = relationship('Subtask', backref='task', cascade='all, delete-orphan')
    tags = relationship('Tag', secondary=task_tags, lazy='joined', backref='tasks')

class TaskNote(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey('task.id'), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

class TaskLink(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey('task.id'), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)  # http(s):// or file:///C:/...
    kind: Mapped[str] = mapped_column(String(20), default='web')  # web | file | app

class Subtask(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey('task.id'), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='todo')  # todo, done

class Event(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)



class GmailAccount(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    token_path: Mapped[str] = mapped_column(Text, nullable=False)

class OutlookAccount(db.Model, TimestampMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    token_path: Mapped[str] = mapped_column(Text, nullable=False)

class Bookmark(db.Model, TimestampMixin):
    __tablename__ = "bookmark"  # optional, but keeps things explicit
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)   # http(s):// or file:///
    kind: Mapped[str] = mapped_column(String(20), default="web")  # web | file | app
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    category = db.Column(db.String(20), default='other', nullable=False)

    # NEW:
    #category: Mapped[str] = mapped_column(String(20), default="other", nullable=False)