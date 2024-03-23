from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def token_required(f):
    """
    A decorator to protect routes that require a token for authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except:
            return jsonify({'message': 'Token is missing or invalid'}), 401
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    """
    Helper function to retrieve the current user based on the JWT token.
    """
    user_id = get_jwt_identity()
    return user_id
