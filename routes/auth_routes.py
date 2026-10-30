from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models import db, User

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        
        if not username_or_email or not password:
            flash('Please provide both username/email and password.', 'danger')
            return render_template('login.html')
            
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            session.permanent = True
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
            
        flash('Invalid credentials. Please verify your username and password.', 'danger')
        
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        monthly_income = float(request.form.get('monthly_income', 4500.0) or 4500.0)
        liquid_savings = float(request.form.get('liquid_savings', 12000.0) or 12000.0)
        risk_tolerance = request.form.get('risk_tolerance', 'moderate')
        
        # Validation
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('register.html')
            
        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
            
        # Check existing
        if User.query.filter_by(username=username).first():
            flash('Username is already registered.', 'danger')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email is already registered.', 'danger')
            return render_template('register.html')
            
        new_user = User(
            username=username,
            email=email,
            full_name=full_name or username,
            monthly_income=monthly_income,
            liquid_savings=liquid_savings,
            risk_tolerance=risk_tolerance
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        session.clear()
        session['user_id'] = new_user.id
        flash('Account created successfully! Welcome to SmartFinance AI.', 'success')
        return redirect(url_for('dashboard.index'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = g.user
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', user.full_name).strip()
        user.monthly_income = float(request.form.get('monthly_income', user.monthly_income) or user.monthly_income)
        user.liquid_savings = float(request.form.get('liquid_savings', user.liquid_savings) or user.liquid_savings)
        user.risk_tolerance = request.form.get('risk_tolerance', user.risk_tolerance)
        user.currency = request.form.get('currency', user.currency)
        
        new_pw = request.form.get('new_password', '').strip()
        if new_pw:
            if len(new_pw) >= 6:
                user.set_password(new_pw)
                flash('Password updated successfully.', 'success')
            else:
                flash('New password must be at least 6 characters.', 'warning')
                
        db.session.commit()
        flash('Profile settings updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('profile.html', user=user)

