
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..extensions import db
from ..models import Task, Tag, TaskNote, TaskLink, Subtask

tasks_bp = Blueprint('tasks', __name__)

def parse_tags(tag_str: str):
    names = [t.strip().lower() for t in (tag_str or '').split(',') if t.strip()]
    uniq = []
    for n in names:
        if n not in uniq:
            uniq.append(n)
    tags = []
    for name in uniq:
        t = Tag.query.filter_by(name=name).first()
        if not t:
            t = Tag(name=name)
            db.session.add(t)
        tags.append(t)
    return tags

@tasks_bp.route('/')
@login_required
def list_tasks():
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    tag = request.args.get('tag', '').strip().lower()
    query = Task.query
    if status:
        query = query.filter(Task.status == status)
    if category:
        query = query.filter(Task.category == category)
    if tag:
        query = query.join(Task.tags).filter(Tag.name == tag)
    tasks = query.order_by(Task.due_at.asc().nullslast(), Task.priority.desc()).all()
    all_tags = Tag.query.order_by(Tag.name.asc()).all()
    return render_template('tasks/list.html', tasks=tasks, status=status, category=category, tag=tag, all_tags=all_tags)

@tasks_bp.route('/new', methods=['GET','POST'])
@login_required
def new_task():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'other')
        priority = int(request.form.get('priority', '0') or 0)
        status = request.form.get('status', 'todo')
        start_at = request.form.get('start_at', '').strip()
        due_at = request.form.get('due_at', '').strip()
        tags_in = request.form.get('tags', '')
        t = Task(title=title, description=description, category=category, priority=priority, status=status)
        if start_at:
            try: t.start_at = datetime.fromisoformat(start_at)
            except: pass
        else:
            t.start_at = datetime.now()
        if due_at:
            try: t.due_at = datetime.fromisoformat(due_at)
            except: pass
        t.tags = parse_tags(tags_in)
        db.session.add(t)
        db.session.commit()
        flash('Task created', 'success')
        return redirect(url_for('tasks.edit_task', tid=t.id))
    preset = datetime.now().replace(second=0, microsecond=0).isoformat()
    return render_template('tasks/edit.html', task=None, preset_start=preset)

@tasks_bp.route('/<int:tid>')
@login_required
def view_task(tid):
    t = Task.query.get_or_404(tid)
    return render_template('tasks/view.html', task=t)

@tasks_bp.route('/<int:tid>/edit', methods=['GET','POST'])
@login_required
def edit_task(tid):
    t = Task.query.get_or_404(tid)
    if request.method == 'POST':
        t.title = request.form.get('title', '').strip()
        t.description = request.form.get('description', '').strip()
        t.status = request.form.get('status', 'todo')
        t.category = request.form.get('category', 'other')
        t.priority = int(request.form.get('priority', '0') or 0)
        start_at = request.form.get('start_at', '').strip()
        due_at = request.form.get('due_at', '').strip()
        tags_in = request.form.get('tags', '')
        if start_at:
            try: t.start_at = datetime.fromisoformat(start_at)
            except: pass
        else:
            t.start_at = None
        if due_at:
            try: t.due_at = datetime.fromisoformat(due_at)
            except: pass
        else:
            t.due_at = None
        t.tags = parse_tags(tags_in)
        db.session.commit()
        flash('Task updated', 'success')
        return redirect(url_for('tasks.edit_task', tid=t.id))
    return render_template('tasks/edit.html', task=t, preset_start=None)

@tasks_bp.route('/<int:tid>/delete', methods=['POST'])
@login_required
def delete_task(tid):
    t = Task.query.get_or_404(tid)
    db.session.delete(t)
    db.session.commit()
    flash('Task deleted', 'info')
    return redirect(url_for('tasks.list_tasks'))

# Notes
@tasks_bp.route('/<int:tid>/notes', methods=['POST'])
@login_required
def add_note(tid):
    t = Task.query.get_or_404(tid)
    body = request.form.get('body', '').strip()
    if body:
        n = TaskNote(task_id=t.id, body=body)
        db.session.add(n)
        db.session.commit()
        flash('Note added','success')
    return redirect(url_for('tasks.edit_task', tid=t.id))

@tasks_bp.route('/<int:tid>/notes/<int:nid>/delete', methods=['POST'])
@login_required
def del_note(tid, nid):
    n = TaskNote.query.get_or_404(nid)
    db.session.delete(n)
    db.session.commit()
    flash('Note deleted','info')
    return redirect(url_for('tasks.edit_task', tid=tid))

# Links
@tasks_bp.route('/<int:tid>/links', methods=['POST'])
@login_required
def add_link(tid):
    t = Task.query.get_or_404(tid)
    title = request.form.get('title','').strip() or 'Link'
    url = request.form.get('url','').strip()
    kind = request.form.get('kind','web')
    if url:
        if kind == 'file' and not url.startswith('file:///'):
            p = url.replace('\\\\','/').replace('\\','/')
            if ':' in p[:3]:
                url = 'file:///' + p
        l = TaskLink(task_id=t.id, title=title, url=url, kind=kind)
        db.session.add(l)
        db.session.commit()
        flash('Link added','success')
    return redirect(url_for('tasks.edit_task', tid=t.id))

@tasks_bp.route('/<int:tid>/links/<int:lid>/edit', methods=['GET','POST'])
@login_required
def edit_link(tid, lid):
    t = Task.query.get_or_404(tid)
    l = TaskLink.query.get_or_404(lid)
    if request.method == 'POST':
        l.title = request.form.get('title','').strip() or l.title
        l.url = request.form.get('url','').strip() or l.url
        l.kind = request.form.get('kind','web')
        if l.kind == 'file' and l.url and not l.url.startswith('file:///'):
            p = l.url.replace('\\\\','/').replace('\\','/')
            if ':' in p[:3]:
                l.url = 'file:///' + p
        db.session.commit()
        flash('Link updated','success')
        return redirect(url_for('tasks.edit_task', tid=t.id))
    return render_template('tasks/edit_link.html', task=t, link=l)

@tasks_bp.route('/<int:tid>/links/<int:lid>/delete', methods=['POST'])
@login_required
def del_link(tid, lid):
    l = TaskLink.query.get_or_404(lid)
    db.session.delete(l)
    db.session.commit()
    flash('Link removed','info')
    return redirect(url_for('tasks.edit_task', tid=tid))

# Subtasks
@tasks_bp.route('/<int:tid>/subtasks', methods=['POST'])
@login_required
def add_subtask(tid):
    t = Task.query.get_or_404(tid)
    title = request.form.get('title','').strip()
    if title:
        s = Subtask(task_id=t.id, title=title, status='todo')
        db.session.add(s)
        db.session.commit()
        flash('Subtask added','success')
    return redirect(url_for('tasks.edit_task', tid=t.id))

@tasks_bp.route('/<int:tid>/subtasks/<int:sid>/toggle', methods=['POST'])
@login_required
def toggle_subtask(tid, sid):
    s = Subtask.query.get_or_404(sid)
    s.status = 'done' if s.status != 'done' else 'todo'
    db.session.commit()
    return redirect(url_for('tasks.edit_task', tid=tid))

@tasks_bp.route('/<int:tid>/subtasks/<int:sid>/delete', methods=['POST'])
@login_required
def del_subtask(tid, sid):
    s = Subtask.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    flash('Subtask deleted','info')
    return redirect(url_for('tasks.edit_task', tid=tid))
