from flask import Flask
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json  # Import json to parse the environment variable

db = None

def initialize_firebase():
    global db
    
    if not firebase_admin._apps:
        # OPTION 1: Try fetching from Environment Variable (For Render Deployment)
        firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
        
        if firebase_creds:
            try:
                # Parse the JSON string from the environment variable
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print("Firebase Initialized from Environment Variable")
                return # Exit function, success
            except Exception as e:
                print(f"Failed to initialize from Env Var: {e}")

        # OPTION 2: Fallback to local file (For Local Development)
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')

        if os.path.exists(cred_path):
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print("Firebase Initialized from Local File")
            except Exception as e:
                print(f"Failed to initialize Firebase from file: {e}")
        else:
            # If neither works, print an error (but don't crash app immediately, though DB won't work)
            print("Error: No Firebase credentials found (Env Var or File).")
    else:
        db = firestore.client()

initialize_firebase()

def create_app():
    app = Flask(__name__)
    # It is also good practice to use an Env Var for the Secret Key
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'GHSTGFYUJSGFDVBER')

    # Security settings (Ensure these don't break local dev, usually fine)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    CORS(app)

    from .auth import auth
    from .views import views

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')

    return app