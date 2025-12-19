from flask import Blueprint, render_template,send_from_directory, session, redirect, url_for

views= Blueprint ('views', __name__)

@views.route('/')
def login_page():
    if 'user' in session:
        return redirect (url_for('views.dashboard'))
    return render_template('index.html')

@views.route('/register')
def register():
    if 'user' in session:
        return redirect(url_for('views.dashboard'))
    return render_template('signup.html')

@views.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('views.login_page'))
    
    return render_template('home.html',user_name=session.get('user_name'))

@views.route('/sw.js')
def service_worker():
    return send_from_directory('static','sw.js')