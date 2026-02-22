"""Authentication routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('projects.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = AuthService.authenticate(username, password)
        if user:
            login_user(user)
            return redirect(url_for('projects.index'))
        flash('Invalid username or password.', 'error')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('projects.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user, error = AuthService.register(username, email, password)
        if user:
            login_user(user)
            return redirect(url_for('projects.index'))
        flash(error, 'error')
    return render_template('auth/register.html')
