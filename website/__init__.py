from flask import Flask
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
 
cred_path = os.path.join(os.path.dirname(__file__),'serviceAccountKey.json')
cred= credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db= firestore.client()


def create_app():
    app= Flask(__name__)
    app.config['SECRET_KEY']= 'GHSTGFYUJSGFDVBER'

    
    CORS (app)

    from .auth import auth 
    from .views import views

    app.register_blueprint(auth,url_prefix='/')
    app.register_blueprint(views,url_prefix='/')
    
    return app