import os
import logging
import pymongo
from flask import Flask, request, abort, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from bson import json_util, ObjectId
from dotenv import load_dotenv

# load env
load_dotenv()

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
mongo = PyMongo(app)

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(app)


@app.before_request
def log_request_info():
    logger.info(
        f"Request: {request.method} {request.url} - Data: {request.json}")


def handle_db_call(call):
    try:
        return call()
    except pymongo.errors.ServerSelectionTimeoutError:
        logger.error("Database connection timeout")
        abort(503, "Database connection timeout")


@app.route('/health-check', methods=['GET'])
def healthcheck():
    return "OK", 200


@app.route('/api/register', methods=['POST'])
def register():
    users = mongo.db.users
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    if users.find_one({"username": username}):
        return jsonify({"msg": "Username already exists"}), 409

    users.insert_one({"username": username, "password": password})
    return jsonify({"msg": "User registered successfully"}), 201


@app.route('/api/login', methods=['POST'])
def login():
    users = mongo.db.users
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    user = users.find_one({"username": username, "password": password})

    if not user:
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


@app.route('/api/check_username', methods=['GET'])
def check_username():
    username = request.args.get('username')
    user_exists = mongo.db.users.find_one({"username": username})
    return jsonify({"available": not bool(user_exists)}), 200


@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        products = handle_db_call(lambda: list(mongo.db.products.find()))
        return json_util.dumps(products)
    except Exception as e:
        logger.error(f"Failed to retrieve products: {e}")
        abort(500, "Internal Server Error")


@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = handle_db_call(
            lambda: mongo.db.products.find_one_or_404({'_id': ObjectId(product_id)}))
        return json_util.dumps(product)
    except Exception as e:
        logger.error(f"Failed to retrieve product {product_id}: {e}")
        abort(500, "Internal Server Error")


@app.route('/api/products', methods=['POST'])
@jwt_required()
def create_product():
    try:
        current_user = get_jwt_identity()
        product_data = request.json
        if 'user' not in product_data or product_data['user'] != current_user:
            abort(403, "Unauthorized: User mismatch")

        if not all(key in product_data for key in ['user', 'description']):
            abort(400, "Missing required fields for product listing")
        product_id = handle_db_call(
            lambda: mongo.db.products.insert_one(product_data).inserted_id)
        return json_util.dumps({"message": "Product created successfully", "product_id": str(product_id)}), 201
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        abort(500, "Internal Server Error")


@app.route('/api/services', methods=['GET'])
def get_services():
    try:
        services = handle_db_call(lambda: list(mongo.db.services.find()))
        return json_util.dumps(services)
    except Exception as e:
        logger.error(f"Failed to retrieve services: {e}")
        abort(500, "Internal Server Error")


@app.route('/api/services/<service_id>', methods=['GET'])
def get_service(service_id):
    try:
        service = handle_db_call(
            lambda: mongo.db.services.find_one_or_404({'_id': ObjectId(service_id)}))
        return json_util.dumps(service)
    except Exception as e:
        logger.error(f"Failed to retrieve service {service_id}: {e}")
        abort(500, "Internal Server Error")


@app.route('/api/services', methods=['POST'])
@jwt_required()
def create_service():
    try:
        current_user = get_jwt_identity()
        service_data = request.json
        if 'user' not in service_data or service_data['user'] != current_user:
            abort(403, "Unauthorized: User mismatch")

        if not all(key in service_data for key in ['user', 'description']):
            abort(400, "Missing required fields for service")
        service_id = handle_db_call(
            lambda: mongo.db.services.insert_one(service_data).inserted_id)
        return json_util.dumps({"message": "Service created successfully", "service_id": str(service_id)}), 201
    except Exception as e:
        logger.error(f"Failed to create service: {e}")
        abort(500, "Internal Server Error")


@app.route('/api/appointments/<service_id>', methods=['GET'])
def get_appointments_for_service(service_id):
    try:
        appointments = handle_db_call(lambda: list(
            mongo.db.appointments.find({'service_id': service_id})))
        return json_util.dumps(appointments)

    except Exception as e:
        logger.error(
            f"Failed to retrieve appointments for service {service_id}: {e}")
        abort(500, "Internal Server Error")


@app.route('/api/appointments', methods=['POST'])
@jwt_required()
def book_appointment():
    try:
        current_user = get_jwt_identity()
        appointment_data = request.json
        if 'user' not in appointment_data or appointment_data['user'] != current_user:
            abort(403, "Unauthorized: User mismatch")

        if not all(key in appointment_data for key in ['service_id', 'timeslot', 'user']):
            abort(400, "Missing required fields for appointment")

        service = handle_db_call(lambda: mongo.db.services.find_one(
            {'_id': ObjectId(appointment_data['service_id'])}))

        if not service:
            abort(404, "Service not found")

        existing_appointment = handle_db_call(lambda: mongo.db.appointments.find_one({
            'service_id': appointment_data['service_id'],
            'timeslot': appointment_data['timeslot']
        }))

        if existing_appointment:
            abort(409, "Appointment already booked for this timeslot")

        appointment_id = handle_db_call(
            lambda: mongo.db.appointments.insert_one(appointment_data).inserted_id)
        return json_util.dumps({"message": "Appointment booked successfully", "appointment_id": str(appointment_id)}), 200
    except Exception as e:
        logger.error(f"Failed to book appointment: {e}")
        abort(500, "Internal Server Error")
