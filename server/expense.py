from flask import Blueprint, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from models import create_expense, update_expense
from extensions import mongo
from utils import token_required



expense_blueprint = Blueprint('expense', __name__)

@expense_blueprint.route('/', methods=['POST'])
@jwt_required()
def add_expense():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('description') or not data.get('amount'):
        return jsonify({'message': 'Must provide description and amount'}), 400
    
    expense_data = create_expense(user_id, data['description'], data['amount'], data.get('category'))
    mongo.db.expenses.insert_one(expense_data)
    
    return jsonify({'message': 'Expense added successfully'}), 201

@expense_blueprint.route('/', methods=['GET'])
@jwt_required()
def get_expenses():
    user_id = get_jwt_identity()
    expenses = mongo.db.expenses.find({'user_id': ObjectId(user_id)})
    return jsonify([expense for expense in expenses]), 200

@expense_blueprint.route('/<expense_id>', methods=['GET'])
@jwt_required()
def get_single_expense(expense_id):
    user_id = get_jwt_identity()
    expense = mongo.db.expenses.find_one({'_id': ObjectId(expense_id), 'user_id': ObjectId(user_id)})
    
    if not expense:
        return jsonify({'message': 'Expense not found'}), 404
    
    return jsonify(expense), 200

@expense_blueprint.route('/<expense_id>', methods=['PUT'])
@jwt_required()
def update_expense_route(expense_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    expense = mongo.db.expenses.find_one({'_id': ObjectId(expense_id), 'user_id': ObjectId(user_id)})
    
    if not expense:
        return jsonify({'message': 'Expense not found'}), 404
    
    updated_expense = update_expense(expense, **data)
    mongo.db.expenses.update_one({'_id': ObjectId(expense_id)}, {"$set": updated_expense})
    
    return jsonify({'message': 'Expense updated successfully'}), 200

@expense_blueprint.route('/<expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    user_id = get_jwt_identity()
    result = mongo.db.expenses.delete_one({'_id': ObjectId(expense_id), 'user_id': ObjectId(user_id)})
    
    if result.deleted_count == 0:
        return jsonify({'message': 'Expense not found'}), 404
    
    return jsonify({'message': 'Expense deleted successfully'}), 200


@expense_blueprint.route('/expenses/stats', methods=['GET'])

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

