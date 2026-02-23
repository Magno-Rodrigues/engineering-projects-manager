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


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Handle password reset via token."""
    if request.method == 'GET':
        token = request.args.get('token', '')
        if not token:
            flash('Link de redefinição inválido.', 'error')
            return redirect(url_for('auth.login'))
        from app.services.token_service import TokenService
        user, error = TokenService.verify_reset_token(token)
        if not user:
            flash(error, 'error')
            return redirect(url_for('auth.login'))
        return render_template('auth/reset_password.html', token=token)

    token = request.form.get('token', '')
    password = request.form.get('password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    from app.services.token_service import TokenService
    user, error = TokenService.verify_reset_token(token)
    if not user:
        flash(error, 'error')
        return redirect(url_for('auth.login'))

    if not password:
        flash('A senha não pode estar em branco.', 'error')
        return render_template('auth/reset_password.html', token=token)
    if password != confirm_password:
        flash('As senhas não conferem.', 'error')
        return render_template('auth/reset_password.html', token=token)

    user.set_password(password)
    TokenService.invalidate_reset_token(user)
    flash('Senha definida com sucesso! Faça o login.', 'success')
    return redirect(url_for('auth.login'))
