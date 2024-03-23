# app.py
from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Initialize extensions without passing the app
mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://localhost:27017/expensesDatabase"
    app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"
    
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Bind extensions to the app
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Import and register blueprints inside the function to avoid circular imports
    from user import user_blueprint
    app.register_blueprint(user_blueprint, url_prefix='/user')

    from expense import expense_blueprint
    app.register_blueprint(expense_blueprint, url_prefix='/expenses')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
