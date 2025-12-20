from flask import Flask
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os

db=None

def initialize_firebase():
    global db
    
    if not firebase_admin._apps:
        cred_path=os.path.join(os.path.dirname(__file__),'serviceAccountKey.json')

        if os.path.exists(cred_path):
            try:
                cred=credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                db=firestore.client()
                print("Firebase Initialized Successfully")
            except Exception as e:
                print(f"Failed to initialize Firebase:{e}")
        else:
            print(f"Error: serviceAccountKey.json not found at {cred_path}")
    else:
        db+firestore.client()

initialize_firebase()

def create_app():
    app=Flask(__name__)
    app.config['SECRET_KEY']= 'GHSTGFYUJSGFDVBER'

    app.config['SESSION_COOKIE_SECURE']= True
    app.config['SESSION_COOKIE_SAMESITE']= 'Lax'

    CORS(app)

    from .auth import auth
    from .views import views

    app.register_blueprint(auth,url_prefix='/')
    app.register_blueprint(views,url_prefix='/')

    return app
