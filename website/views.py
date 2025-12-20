from flask import Blueprint, render_template, send_from_directory, session, redirect, url_for, request, current_app
from . import db
from firebase_admin import firestore
import os
from werkzeug.utils import secure_filename

views = Blueprint('views', __name__)

UPLOAD_FOLDER = 'website/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/')
def home():
    user_name = session.get('user_name') if 'user' in session else None
    return render_template('home.html', user_name=user_name)

@views.route('/dashboard')
def dashboard():
    return redirect(url_for('views.home'))

@views.route('/login')
def login_page():
    if 'user' in session:
        return redirect(url_for('views.home'))
    return render_template('index.html')

@views.route('/register')
def register():
    if 'user' in session:
        return redirect(url_for('views.home'))
    return render_template('signup.html')

@views.route('/profile')
def profile():
    user_info = None
    if 'user' in session:
        user_info = {
            'full_name': session.get('user_name', 'Farmer'),
            'phone_number': session.get('user'),
            'role': 'Farmer'
        }
    return render_template('profile.html', user=user_info)

@views.route('/logout')
def logout():
    session.clear()
    return {'success': True}

# --- MARKETPLACE (BUYING) ---
@views.route('/marketplace', methods=['GET', 'POST'])
def marketplace():
    products_ref = db.collection('marketplace_items')

    # Handle Selling Logic
    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('views.login_page'))
            
        try:
            name = request.form.get('name')
            price = request.form.get('price')
            unit = request.form.get('unit')
            location = request.form.get('location')
            category = request.form.get('category')
            description = request.form.get('description')
            
            image_url = "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=400&q=80"
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    image_url = url_for('static', filename=f'uploads/{filename}')

            new_item = {
                'name': name,
                'price': int(price) if price else 0,
                'unit': unit,
                'location': location,
                'category': category,
                'description': description,
                'seller': session.get('user_name'),
                'seller_phone': session.get('user'),
                'image': image_url,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            products_ref.add(new_item)
            return redirect(url_for('views.marketplace'))
        except Exception as e:
            print(f"Error adding item: {e}")

    # Handle Search & Filter
    search_query = request.args.get('search', '').lower()
    filter_category = request.args.get('category', '')
    filter_location = request.args.get('location', '').lower()
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    products_list = []
    try:
        docs = products_ref.stream()
        for doc in docs:
            item = doc.to_dict()
            item['id'] = doc.id
            
            if search_query and search_query not in item.get('name', '').lower(): continue
            if filter_category and filter_category != 'All' and filter_category != item.get('category', ''): continue
            if filter_location and filter_location not in item.get('location', '').lower(): continue
            
            price = item.get('price', 0)
            if min_price and price < int(min_price): continue
            if max_price and price > int(max_price): continue

            products_list.append(item)
    except Exception as e:
        print(f"Database Error: {e}")

    return render_template('marketplace.html', products=products_list, user_logged_in=('user' in session))

# --- MY FARM (MANAGING) ---
@views.route('/myfarm')
def my_farm():
    if 'user' not in session:
        return redirect(url_for('views.login_page'))
    
    products_ref = db.collection('marketplace_items')
    try:
        query = products_ref.where('seller_phone', '==', session.get('user')).stream()
        my_products = []
        for doc in query:
            item = doc.to_dict()
            item['id'] = doc.id
            my_products.append(item)
            
    except Exception as e:
        print(f"Error fetching farm items: {e}")
        my_products = []

    return render_template('my_farm.html', products=my_products, user=session.get('user_name'))

# --- EDIT ITEM ROUTE ---
@views.route('/marketplace/edit/<string:item_id>', methods=['POST'])
def edit_item(item_id):
    if 'user' not in session: return redirect(url_for('views.login_page'))
    
    doc_ref = db.collection('marketplace_items').document(item_id)
    doc = doc_ref.get()
    
    if doc.exists:
        item = doc.to_dict()
        if item.get('seller_phone') == session.get('user'):
            try:
                updates = {
                    'name': request.form.get('name'),
                    'price': int(request.form.get('price')),
                    'unit': request.form.get('unit'),
                    'location': request.form.get('location'),
                    'category': request.form.get('category'),
                    'description': request.form.get('description'),
                    'updated_at': firestore.SERVER_TIMESTAMP
                }
                # Handle Image Update
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        if not os.path.exists(UPLOAD_FOLDER):
                            os.makedirs(UPLOAD_FOLDER)
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(file_path)
                        updates['image'] = url_for('static', filename=f'uploads/{filename}')

                doc_ref.update(updates)
            except Exception as e:
                print(f"Error updating: {e}")
    
    return redirect(url_for('views.my_farm'))

# --- DELETE ITEM ROUTE ---
@views.route('/marketplace/delete/<string:item_id>', methods=['POST'])
def delete_item(item_id):
    if 'user' not in session: return redirect(url_for('views.login_page'))
    try:
        doc_ref = db.collection('marketplace_items').document(item_id)
        doc = doc_ref.get()
        if doc.exists and doc.to_dict().get('seller_phone') == session.get('user'):
            doc_ref.delete()
    except Exception as e:
        print(f"Error: {e}")
    return redirect(url_for('views.my_farm'))

@views.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js')

# Placeholder routes
@views.route('/disease-detection')
def disease_detection(): return "<h3>Coming Soon</h3><a href='/'>Back Home</a>"
@views.route('/community')
def community(): return "<h3>Coming Soon</h3><a href='/'>Back Home</a>"
@views.route('/news')
def news(): return "<h3>Coming Soon</h3><a href='/'>Back Home</a>"
@views.route('/mandi')
def mandi(): return "<h3>Coming Soon</h3><a href='/'>Back Home</a>"