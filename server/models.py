from flask_bcrypt import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

def create_user(username, email, password):
    """
    Create a user dictionary with a hashed password to store in the database.
    """
    password_hash = generate_password_hash(password).decode('utf-8')
    return {
        "username": username,
        "email": email,
        "password": password_hash
    }

def verify_user(user, password):
    """
    Check the provided password against the hashed password in the database.
    """
    return check_password_hash(user['password'], password)

def create_expense(user_id, description, amount, category):
    """
    Create an expense dictionary to store in the database.
    """
    return {
        "user_id": ObjectId(user_id),  # Ensure the user_id is stored as an ObjectId
        "description": description,
        "amount": float(amount),  # Convert the amount to a float
        "category": category
    }

def update_expense(expense, description=None, amount=None, category=None):
    """
    Update the expense dictionary with new values provided.
    """
    if description is not None:
        expense['description'] = description
    if amount is not None:
        expense['amount'] = float(amount)  # Convert the amount to a float
    if category is not None:
        expense['category'] = category
    return expense
