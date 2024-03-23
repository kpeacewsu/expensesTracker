from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_pymongo import PyMongo
from models import create_user, verify_user
from extensions import mongo,bcrypt, jwt


user_blueprint = Blueprint('user', __name__)

@user_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Must provide username, email, and password'}), 400
    email = mongo.db.users.find_one({'email': data['email']})
    if email is None:
        pass;
    else:
        return jsonify({'message': 'Email already exists'}), 409

    user = create_user(data['username'], data['email'], data['password'])
    mongo.db.users.insert_one(user)

    return jsonify({'message': 'User registered successfully'}), 201

@user_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Must provide email and password'}), 400

    user = mongo.db.users.find_one({'email': data['email']})
    if user and verify_user(user, data['password']):
        access_token = create_access_token(identity=str(user['_id']))
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401
