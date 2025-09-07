
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from ..extensions import db
from ..models import Event

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/')
@login_required
def list_events():
    events = Event.query.order_by(Event.start_at.asc().nullslast()).all()
    return render_template('calendar/list.html', events=events)

@calendar_bp.route('/new', methods=['GET','POST'])
@login_required
def new_event():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        start_at = request.form.get('start_at', '').strip()
        end_at = request.form.get('end_at', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        e = Event(title=title, location=location, description=description)
        if start_at:
            try: e.start_at = datetime.fromisoformat(start_at)
            except: pass
        if end_at:
            try: e.end_at = datetime.fromisoformat(end_at)
            except: pass
        db.session.add(e)
        db.session.commit()
        flash('Event created', 'success')
        return redirect(url_for('calendar.list_events'))
    return render_template('calendar/edit.html', event=None)

@calendar_bp.route('/<int:eid>/edit', methods=['GET','POST'])
@login_required
def edit_event(eid):
    e = Event.query.get_or_404(eid)
    if request.method == 'POST':
        e.title = request.form.get('title', '').strip()
        e.location = request.form.get('location', '').strip()
        e.description = request.form.get('description', '').strip()
        start_at = request.form.get('start_at', '').strip()
        end_at = request.form.get('end_at', '').strip()
        if start_at:
            try: e.start_at = datetime.fromisoformat(start_at)
            except: pass
        else:
            e.start_at = None
        if end_at:
            try: e.end_at = datetime.fromisoformat(end_at)
            except: pass
        else:
            e.end_at = None
        db.session.commit()
        flash('Event updated', 'success')
        return redirect(url_for('calendar.list_events'))
    return render_template('calendar/edit.html', event=e)

@calendar_bp.route('/<int:eid>/delete', methods=['POST'])
@login_required
def delete_event(eid):
    e = Event.query.get_or_404(eid)
    db.session.delete(e)
    db.session.commit()
    flash('Event deleted', 'info')
    return redirect(url_for('calendar.list_events'))

@calendar_bp.route('/full')
@login_required
def full_view():
    return render_template('calendar/full.html')

@calendar_bp.route('/feed.json')
@login_required
def feed_events_json():
    items = Event.query.all()
    def to_iso(dt):
        return dt.isoformat() if dt else None
    events = []
    for e in items:
        events.append({
            "id": e.id,
            "title": e.title,
            "start": to_iso(e.start_at),
            "end": to_iso(e.end_at),
            "extendedProps": {"location": e.location or "", "description": e.description or ""}
        })
    return jsonify(events)
