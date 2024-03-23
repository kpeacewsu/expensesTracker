from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager,jwt_required, get_jwt_identity
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB setup
app.config["MONGO_URI"] = "mongodb://localhost:27017/expensesDatabase"
mongo = PyMongo(app)

# Initialize Bcrypt and JWT Manager
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'

def create_expense(user_id, description, amount, category):
    return {
        "user_id": user_id,
        "description": description,
        "amount": amount,
        "category": category
    }

def create_user(username, email, password):
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    return {
        "username": username,
        "email": email,
        "password": password_hash
    }

# Routes
@app.route('/expenses', methods=['POST'])
@jwt_required()
def handle_expenses():
    if request.method == 'POST':
        if request.is_json:
            user_id = get_jwt_identity()
            data = request.get_json()
            expense = create_expense(user_id,data['description'], data['amount'], data.get('category'))
            mongo.db.expenses.insert_one(expense)
            return {"message": "Expense has been created successfully."}, 201
        else:
            return {"error": "The request payload is not in JSON format"}, 400


@app.route('/expenses/<expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    if request.is_json:
        try:
            update_data = request.get_json()
            # MongoDB update result
            result = mongo.db.expenses.update_one(
                {"_id": ObjectId(expense_id)},
                {"$set": update_data}
            )

            if result.matched_count == 0:
                return jsonify({"error": "Expense not found"}), 404
            if result.modified_count == 0:
                return jsonify({"message": "No changes made to the expense"}), 200
            return jsonify({"message": "Expense updated successfully"}), 200
        except:
            return jsonify({"error": "Invalid expense ID format or update data"}), 400
    else:
        return jsonify({"error": "The request payload is not in JSON format"}), 400

@app.route('/expenses/<expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    try:
        result = mongo.db.expenses.delete_one({"_id": ObjectId(expense_id)})

        if result.deleted_count == 0:
            return jsonify({"error": "Expense not found"}), 404
        
        return jsonify({"message": "Expense successfully deleted"}), 200
    except:
        return jsonify({"error": "Invalid expense ID format"}), 400

@app.route('/expenses/<expense_id>', methods=['GET'])
@jwt_required()
def get_expense(expense_id):
    try:
        expense = mongo.db.expenses.find_one({"_id": ObjectId(expense_id)})
        if expense:
            expense["_id"] = str(expense["_id"])  # Convert ObjectId to string for JSON serialization
            return jsonify(expense), 200
        else:
            return jsonify({"error": "Expense not found"}), 404
    except:
        return jsonify({"error": "Invalid expense ID format"}), 400


@app.route('/expenses', methods=['GET'])
@jwt_required()
def getAll_expenses():
    if request.method == 'GET':
        expenses_cursor = mongo.db.expenses.find()
        expenses = list(expenses_cursor)
        
        # Convert each ObjectId to string for JSON serialization
        for expense in expenses:
            expense["_id"] = str(expense["_id"])
        
        return {"count": len(expenses), "expenses": expenses}, 200

@app.route('/expenses/stats', methods=['GET'])
@jwt_required()
def get_expense_stats():
    # Aggregate total spent
    total_spent_aggregation = mongo.db.expenses.aggregate([
        {
            "$addFields": {
                "amountNumeric": {"$toDouble": "$amount"}
            }
        },
        {
            "$group": {
                "_id": None, 
                "total_spent": {"$sum": "$amountNumeric"}
            }
        }
    ])
    total_spent_result = list(total_spent_aggregation)
    total_spent = total_spent_result[0]['total_spent'] if total_spent_result else 0

    # Aggregate spending by category
    spending_by_category_aggregation = mongo.db.expenses.aggregate([
        {
            "$addFields": {
                "amountNumeric": {"$toDouble": "$amount"}
            }
        },
        {
            "$group": {
                "_id": "$category", 
                "total": {"$sum": "$amountNumeric"}
            }
        },
        {
            "$sort": {"total": -1}  # Optional: sort by total amount, descending
        }
    ])
    spending_by_category = [
        {"category": result["_id"], "amount": result["total"]} 
        for result in spending_by_category_aggregation
    ]

    # Prepare and return the response
    expense_stats = {
        "total_spent": total_spent,
        "spending_by_category": spending_by_category
    }
    return jsonify(expense_stats), 200


#registration point
from flask_jwt_extended import create_access_token

@app.route('/register', methods=['POST'])
def register():
    if request.is_json:
        username = request.json.get('username', None)
        email = request.json.get('email', None)
        password = request.json.get('password', None)
        
        if username and email and password:
            # Ensure that the email is not already in use
            if mongo.db.users.find_one({"email": email}):
                return jsonify(message="A user with that email already exists"), 409

            user_data = create_user(username, email, password)
            mongo.db.users.insert_one(user_data)
            return jsonify(message="User created successfully"), 201
        else:
            return jsonify(message="Missing username, email, or password"), 400
    else:
        return jsonify(message="Payload is not in JSON format"), 400

#login page
@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json.get('email', None)
        password = request.json.get('password', None)

        if email and password:
            user = mongo.db.users.find_one({"email": email})
            if user and bcrypt.check_password_hash(user['password'], password):
                access_token = create_access_token(identity=str(user['_id']))
                return jsonify(access_token=access_token), 200
            else:
                return jsonify(message="Bad username or password"), 401
        else:
            return jsonify(message="Missing email or password"), 400
    else:
        return jsonify(message="Payload is not in JSON format"), 400

# Command to run the server
if __name__ == '__main__':
    app.run(debug=True)
