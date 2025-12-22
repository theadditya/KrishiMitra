from flask import Blueprint, render_template, send_from_directory, session, redirect, url_for, request, current_app, jsonify
from . import db
from firebase_admin import firestore
import os
import requests
import json
from werkzeug.utils import secure_filename
from datetime import datetime, date
from dotenv import load_dotenv  # Import to load .env file

# Load environment variables from .env file
load_dotenv()

views = Blueprint('views', __name__)

UPLOAD_FOLDER = 'website/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/')
def home():
    user_name = session.get('user_name') if 'user' in session else None
    
    # Real-time Data Fetching
    farmer_count = 0
    market_count = 0
    
    try:
        farmer_count = len(list(db.collection('users').stream()))
        market_count = len(list(db.collection('marketplace_items').stream()))
    except Exception as e:
        print(f"Error fetching stats: {e}")

    return render_template('home.html', user_name=user_name, farmer_count=farmer_count, market_count=market_count)

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

    search_query = request.args.get('search', '').lower()
    filter_category = request.args.get('category', '')
    filter_location = request.args.get('location', '').lower()
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    products_list = []
    try:
        docs = products_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
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

# --- COMMUNITY ROUTES ---
@views.route('/community')
def community():
    posts_list = []
    heroes_list = []
    
    # 1. Fetch Posts
    try:
        posts_ref = db.collection('community_posts')
        docs = posts_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        for doc in docs:
            post = doc.to_dict()
            post['id'] = doc.id
            if 'timestamp' in post and post['timestamp']:
                post['time_ago'] = post['timestamp'].strftime('%d %b %Y')
            posts_list.append(post)
    except Exception as e:
        print(f"Error fetching posts: {e}")

    # 2. Fetch Harvest Heroes (Top 3 by score)
    try:
        users_ref = db.collection('users')
        # Order by community_score descending, limit 3
        hero_docs = users_ref.order_by('community_score', direction=firestore.Query.DESCENDING).limit(3).stream()
        
        for doc in hero_docs:
            hero = doc.to_dict()
            # If score doesn't exist, default to 0
            hero['score'] = hero.get('community_score', 0)
            heroes_list.append(hero)
    except Exception as e:
        print(f"Error fetching heroes: {e}")

    return render_template('community.html', posts=posts_list, heroes=heroes_list, user=('user' in session))

@views.route('/community/post', methods=['POST'])
def create_post():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        tag = data.get('tag', 'General')
        phone = session.get('user')
        
        # --- HARVEST HERO SCORE CALCULATION ---
        users_ref = db.collection('users')
        query = users_ref.where('phone_number', '==', phone).stream()
        user_doc = None
        user_id = None
        
        for doc in query:
            user_doc = doc.to_dict()
            user_id = doc.id
            break
            
        if user_doc and user_id:
            current_score = user_doc.get('community_score', 0)
            last_post_date = user_doc.get('last_post_date') # Firestore timestamp
            
            today = datetime.now().date()
            
            points_change = 0
            
            if last_post_date:
                # Convert Firestore timestamp to date
                last_date = last_post_date.date()
                delta = (today - last_date).days
                
                if delta > 0:
                    # It's a new day!
                    # 1. Deduct points for missed days (if any)
                    missed_days = delta - 1
                    if missed_days > 0:
                        points_change -= missed_days
                    
                    # 2. Add points for posting today (First post of the day)
                    points_change += 2
            else:
                # First ever post
                points_change += 2
                
            # Apply Score Update
            new_score = current_score + points_change
            
            # Update User Doc
            users_ref.document(user_id).update({
                'community_score': new_score,
                'last_post_date': firestore.SERVER_TIMESTAMP
            })

        # --- CREATE POST ---
        new_post = {
            'author': session.get('user_name', 'Farmer'),
            'author_id': phone,
            'title': title,
            'content': content,
            'tag': tag,
            'likes': 0,
            'comments': [],
            'timestamp': firestore.SERVER_TIMESTAMP,
            'avatar': f"https://api.dicebear.com/7.x/avataaars/svg?seed={session.get('user_name')}"
        }
        
        db.collection('community_posts').add(new_post)
        
        return jsonify({'success': True, 'message': 'Post created!'})
    except Exception as e:
        print(f"Error creating post: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@views.route('/community/like/<string:post_id>', methods=['POST'])
def like_post(post_id):
    try:
        post_ref = db.collection('community_posts').document(post_id)
        post_ref.update({'likes': firestore.Increment(1)})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@views.route('/community/comment/<string:post_id>', methods=['POST'])
def comment_post(post_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    try:
        data = request.get_json()
        comment_text = data.get('comment')
        
        comment = {
            'author': session.get('user_name'),
            'text': comment_text,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        post_ref = db.collection('community_posts').document(post_id)
        post_ref.update({'comments': firestore.ArrayUnion([comment])})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@views.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js')

# --- DISEASE DETECTION (Updated) ---
@views.route('/disease-detection')
def disease_detection():
    # # Pass API key securely to the frontend
    # api_key = os.environ.get('GEMINI_API_KEY')
    return render_template('disease_detection.html', )

@views.route('api/analyze-crop',methods=['POST'] )
def analyze_crop():
    api_key=os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'Server configuration error: API key is missing'}),500
    
    data=request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
    image_data=data.get('image')
    if not image_data:
        return jsonify({'error':'No images data provide'}),400
    
   
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = """
    You are an expert agricultural plant pathologist. Analyze this image of a crop/plant.
    1. Identify if there is a disease, pest, or if it is healthy.
    2. If diseased, name the disease and explain the symptoms visible.
    3. Provide a confidence score (0-100) based on visual clarity.
    4. Suggest 7 practical treatments or preventative measures.
    5. Answer with respect to an Indian Farmer. You can use simple language and provide practical solutions with Indian Solution too.
    
    Return ONLY valid JSON in this format, with no markdown formatting:
    {
        "name": "Disease Name or 'Healthy'",
        "description": "Brief description of the issue.",
        "confidence": 85,
        "treatments": ["Treatment 1", "Treatment 2", "Treatment 3", "Treatment 4", "Treatment 5", "Treatment 6", "Treatment 7"]
    }
    """

    payload = {
        "contents": [{
            "parts": [
                { "text": prompt },
                { "inline_data": { "mime_type": "image/jpeg", "data": image_data } }
            ]
        }]
    }
    try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            response_data = response.json()
            
            # 4. Parse and Clean the Response on the Server
            if 'candidates' in response_data:
                text_response = response_data['candidates'][0]['content']['parts'][0]['text']
                # Remove Markdown code blocks if present
                clean_json = text_response.replace('```json', '').replace('```', '').strip()
                result = json.loads(clean_json)
                return jsonify(result)
            else:
                print("Gemini API Error:", response_data)
                return jsonify({'error': 'AI could not analyze the image'}), 500

    except Exception as e:
            print(f"Server Error: {e}")
            return jsonify({'error': str(e)}), 500
        
@views.route('/news')
def news(): return "<h3>Coming Soon</h3><a href='/'>Back Home</a>"
@views.route('/mandi')
def mandi(): return "<h3>Coming Soon</h3><a href='/'>Back Home</a>"