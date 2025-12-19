from flask import Blueprint, request, jsonify, session
from . import db
from firebase_admin import firestore

auth = Blueprint ('auth', __name__)

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')

    if not phone or not password:
        return jsonify ({'success': False, 'message': 'Missing data'}), 400
    
    try:
        users_ref= db.collection('users')
        query = users_ref.where ('phone_number','==',phone).stream()

        user_found = None
        for doc in query:
            user_found = doc.to_dict()
            break

        if user_found:
            if user_found.get('password')== password:
                session ['user']= phone
                session ['user_name']= user_found.get('full_name','Farmer')
                return jsonify ({
                'success': True,
                'message': 'Login Succesfully!',
                'user': user_found.get('full_name')
            }), 200
            else:
                return jsonify ({'success': False, 'message': " Invalid password"}),401
        else:
            return jsonify ({'success':False, 'message': 'User not found'}),404

    except Exception as e:
        print(f"Error:{e}")
        return jsonify ({'success': False, 'message': 'Server error'}),500
                        
@auth.route('/signup', methods= ['POST'])
def signup():
    data = request.get_json()
    phone= data.get('phone')
    password= data.get('password')
    full_name= data.get ('full_name')
    dob=data.get('dob')

    if not phone or not password or not full_name:
        return jsonify ({'success': False, 'message': 'Missing required fields'}), 400

    try:
        users_ref= db.collection('users')

        docs= users_ref.where('phone_number','==',phone).stream()
        if any(docs):
            return jsonify ({'success': False, 'message': 'User already exists'}),400
        
        new_user={
            'phone_number': phone,
            'password': password,
            'full_name': full_name,
            'dob': dob,
            'role':'Farmer',
            'created_at': firestore.SERVER_TIMESTAMP
        }
        users_ref.add(new_user)

        session ['user']= phone 
        session['user_name']= full_name

        return jsonify ({'success': True, 'message': 'Account created!'}),201

    except Exception as e:
        print (f"Signup Error: {e}")
        return jsonify ({'success':False, 'message': 'Server Error'}),500
    
    @auth.route ('/logout')
    def logout ():
        session.clear()
        return jsonify({'success': True, 'message':'logged out'})
