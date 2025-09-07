
from flask import Blueprint, render_template
from flask_login import login_required
from ..models import Task, Note, Event

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    open_tasks = Task.query.filter(Task.status != 'done').order_by(Task.due_at.asc().nullslast()).limit(5).all()
    recent_notes = Note.query.order_by(Note.created_at.desc()).limit(5).all()
    upcoming_events = Event.query.order_by(Event.start_at.asc().nullslast()).limit(5).all()
    return render_template('dashboard/index.html', open_tasks=open_tasks, recent_notes=recent_notes, upcoming_events=upcoming_events)
