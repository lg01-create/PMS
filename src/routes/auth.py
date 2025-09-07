
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from passlib.hash import bcrypt
from ..extensions import db
from ..models import User

auth_bp = Blueprint('auth', __name__)

def init_login_manager(login_manager: LoginManager, app):
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.verify(password, user.password_hash):
            login_user(user)
            return redirect(url_for('dashboard.index'))
        flash('Invalid credentials', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'warning')
            return redirect(url_for('auth.register'))
        u = User(email=email, name=name, password_hash=bcrypt.hash(password))
        db.session.add(u)
        db.session.commit()
        flash('Registered. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')
