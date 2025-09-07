
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..extensions import db
from ..models import Note

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/')
@login_required
def list_notes():
    q = request.args.get('q', '').strip()
    query = Note.query
    if q:
        like = f"%{q}%"
        query = query.filter((Note.title.ilike(like)) | (Note.body.ilike(like)))
    notes = query.order_by(Note.created_at.desc()).all()
    return render_template('notes/list.html', notes=notes, q=q)

@notes_bp.route('/new', methods=['GET','POST'])
@login_required
def new_note():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        body = request.form.get('body', '').strip()
        n = Note(title=title, body=body)
        db.session.add(n)
        db.session.commit()
        flash('Note created', 'success')
        return redirect(url_for('notes.list_notes'))
    return render_template('notes/edit.html', note=None)

@notes_bp.route('/<int:nid>/edit', methods=['GET','POST'])
@login_required
def edit_note(nid):
    n = Note.query.get_or_404(nid)
    if request.method == 'POST':
        n.title = request.form.get('title', '').strip()
        n.body = request.form.get('body', '').strip()
        db.session.commit()
        flash('Note updated', 'success')
        return redirect(url_for('notes.list_notes'))
    return render_template('notes/edit.html', note=n)

@notes_bp.route('/<int:nid>/delete', methods=['POST'])
@login_required
def delete_note(nid):
    n = Note.query.get_or_404(nid)
    db.session.delete(n)
    db.session.commit()
    flash('Note deleted', 'info')
    return redirect(url_for('notes.list_notes'))
