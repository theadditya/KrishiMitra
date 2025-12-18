from flask import Blueprint, render_template,send_from_directory

views= Blueprint ('views', __name__)

@views.route('/')
def home():
    return render_template('index.html')

@views.route('/sw.js')
def service_worker():
    return send_from_directory('static','sw.js')