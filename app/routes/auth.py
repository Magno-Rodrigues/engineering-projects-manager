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
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = AuthService.authenticate(username, password)
        if user:
            from datetime import datetime, timezone
            from app import db
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user)
            return redirect(url_for('main.dashboard'))
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


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset via email token."""
    from app.services.email_service import validate_reset_token
    from app.models.reset_token import PasswordResetToken
    from app import db

    user, error = validate_reset_token(token)
    if error:
        flash(error, 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        if not password:
            flash('A senha não pode estar vazia.', 'error')
            return render_template('auth/reset_password.html', token=token)
        if password != confirm:
            flash('As senhas não conferem.', 'error')
            return render_template('auth/reset_password.html', token=token)

        # Mark token as used and update password
        token_obj = PasswordResetToken.query.filter_by(token=token).first()
        token_obj.used = True
        user.set_password(password)
        user.password_reset_required = False
        user.first_login = False
        db.session.commit()

        flash('Senha definida com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@login_required
def reset_password_first_login():
    """Handle in-app password reset for first login (no token required)."""
    from app import db

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        if not password:
            flash('A senha não pode estar vazia.', 'error')
            return render_template('auth/reset_password.html', token=None, first_login=True)
        if password != confirm:
            flash('As senhas não conferem.', 'error')
            return render_template('auth/reset_password.html', token=None, first_login=True)

        current_user.set_password(password)
        current_user.password_reset_required = False
        current_user.first_login = False
        db.session.commit()

        flash('Senha definida com sucesso!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/reset_password.html', token=None, first_login=True)

