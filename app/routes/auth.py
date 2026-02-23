"""Authentication routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import AuthService
from app.utils.decorators import admin_required

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
@login_required
@admin_required
def register():
    """Handle user registration (admin only)."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'engineer')
        user, error = AuthService.register_user_by_admin(
            username, email, password, role=role, admin_id=current_user.id
        )
        if user:
            flash(f'User {user.username} created successfully.', 'success')
            return redirect(url_for('auth.register'))
        flash(error, 'error')
    return render_template('auth/register.html')
