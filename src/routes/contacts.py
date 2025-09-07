
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..extensions import db
from ..models import Contact

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/')
@login_required
def list_contacts():
    q = request.args.get('q', '').strip()
    query = Contact.query
    if q:
        like = f"%{q}%"
        query = query.filter((Contact.name.ilike(like)) | (Contact.email.ilike(like)) | (Contact.phone.ilike(like)))
    contacts = query.order_by(Contact.name.asc()).all()
    return render_template('contacts/list.html', contacts=contacts, q=q)

@contacts_bp.route('/new', methods=['GET','POST'])
@login_required
def new_contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        notes = request.form.get('notes', '').strip()
        c = Contact(name=name, email=email, phone=phone, notes=notes)
        db.session.add(c)
        db.session.commit()
        flash('Contact created', 'success')
        return redirect(url_for('contacts.list_contacts'))
    return render_template('contacts/edit.html', contact=None)

@contacts_bp.route('/<int:cid>/edit', methods=['GET','POST'])
@login_required
def edit_contact(cid):
    c = Contact.query.get_or_404(cid)
    if request.method == 'POST':
        c.name = request.form.get('name', '').strip()
        c.email = request.form.get('email', '').strip()
        c.phone = request.form.get('phone', '').strip()
        c.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Contact updated', 'success')
        return redirect(url_for('contacts.list_contacts'))
    return render_template('contacts/edit.html', contact=c)

@contacts_bp.route('/<int:cid>/delete', methods=['POST'])
@login_required
def delete_contact(cid):
    c = Contact.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    flash('Contact deleted', 'info')
    return redirect(url_for('contacts.list_contacts'))
