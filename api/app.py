import os
import logging
import pymongo
from flask import Flask, request, abort, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from bson import json_util, ObjectId
from dotenv import load_dotenv
from pymongo import ReturnDocument

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
    current_user = get_jwt_identity()
    product_data = request.json
    if 'user' not in product_data or product_data['user'] != current_user:
        return jsonify({"msg": "Unauthorized: User mismatch"}), 403

    required_fields = ['user', 'description', 'price', 'quantity']
    missing_fields = [field for field in required_fields if field not in product_data or not product_data[field]]
    if missing_fields:
        return jsonify({"msg": f"Missing or empty required fields for product listing: {', '.join(missing_fields)}"}), 400
    
    product_id = handle_db_call(
        lambda: mongo.db.products.insert_one(product_data).inserted_id)
    return json_util.dumps({"message": "Product created successfully", "product_id": str(product_id)}), 201


@app.route('/api/purchase_product/<product_id>', methods=['POST'])
@jwt_required()
def purchase_product(product_id):
    current_user = get_jwt_identity()
    
    # Attempt to atomically decrement the quantity if it's greater than 0
    # and ensure the current user is not the seller
    updated_product = mongo.db.products.find_one_and_update(
        {'_id': ObjectId(product_id), 'quantity': {'$gt': 0}, 'user': {'$ne': current_user}},
        {'$inc': {'quantity': -1}},
        return_document=ReturnDocument.AFTER
    )

    if not updated_product:
        # Check if the product exists without applying updates
        product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
        if not product:
            return jsonify({"msg": "Product not found"}), 404
        elif product['user'] == current_user:
            return jsonify({"msg": "Sellers cannot buy their own products"}), 403
        else:
            return jsonify({"msg": "Product is not available"}), 409

    return jsonify({"msg": "Product purchased successfully", "product_id": str(product_id), "new_quantity": updated_product['quantity']}), 200


@app.route('/api/products/<product_id>/is_sold_out', methods=['GET'])
def is_product_sold_out(product_id):
    try:
        product = mongo.db.products.find_one({'_id': ObjectId(product_id)})

        if not product:
            return jsonify({"msg": "Product not found"}), 404
        
        is_sold_out = product.get('quantity', 0) <= 0
        return jsonify({"product_id": str(product_id), "is_sold_out": is_sold_out}), 200

    except Exception as e:
        logger.error(f"Failed to check if product {product_id} is sold out: {e}")
        return jsonify({"msg": "Internal Server Error"}), 500


@app.route('/api/products/<product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    current_user = get_jwt_identity()

    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({"msg": "Product not found"}), 404

    if product['user'] != current_user:
        return jsonify({"msg": "Unauthorized to delete this product"}), 403

    mongo.db.products.delete_one({'_id': ObjectId(product_id)})
    return jsonify({"msg": "Product deleted successfully"}), 200


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
            return jsonify({"msg": "Unauthorized: User mismatch"}), 403

        required_fields = ['user', 'description', 'price', 'available_dates']
        missing_fields = [field for field in required_fields if field not in service_data or not service_data[field]]
        if missing_fields:
            return jsonify({"msg": f"Missing or empty required fields for service listing: {', '.join(missing_fields)}"}), 400
      
        service_id = handle_db_call(
            lambda: mongo.db.services.insert_one(service_data).inserted_id)
        return json_util.dumps({"message": "service created successfully", "service_id": str(service_id)}), 201
    except Exception as e:
        logger.error(f"Failed to create service: {e}")
        abort(500, "Internal Server Error")


@app.route('/api/services/<service_id>', methods=['DELETE'])
@jwt_required()
def delete_service(service_id):
    current_user = get_jwt_identity()

    service = mongo.db.services.find_one({'_id': ObjectId(service_id)})
    if not service:
        return jsonify({"msg": "Service not found"}), 404

    if service['user'] != current_user:
        return jsonify({"msg": "Unauthorized to delete this service"}), 403

    # Delete the service
    mongo.db.services.delete_one({'_id': ObjectId(service_id)})
    
    # Delete all appointments for this service
    mongo.db.appointments.delete_many({'service_id': service_id})

    return jsonify({"msg": "Service and associated appointments deleted successfully"}), 200


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
            return jsonify({"msg": "Unauthorized: User mismatch"}), 403

        if not all(key in appointment_data for key in ['service_id', 'timeslot', 'user']):
            return jsonify({"msg": "Missing required fields for appointment"}), 400

        service = handle_db_call(lambda: mongo.db.services.find_one(
            {'_id': ObjectId(appointment_data['service_id'])}))

        if not service:
            return jsonify({"msg": "Service not found"}), 404

        existing_appointment = handle_db_call(lambda: mongo.db.appointments.find_one({
            'service_id': appointment_data['service_id'],
            'timeslot': appointment_data['timeslot']
        }))

        if existing_appointment:
            return jsonify({"msg":  "Appointment already booked for this timeslot"}), 409

        appointment_id = handle_db_call(
            lambda: mongo.db.appointments.insert_one(appointment_data).inserted_id)
        return json_util.dumps({"message": "Appointment booked successfully", "appointment_id": str(appointment_id)}), 200
    except Exception as e:
        logger.error(f"Failed to book an appointment for service {service_id}: {e}")
        abort(500, "Internal Server Error")

@app.route('/api/bookable_dates/<service_id>', methods=['GET'])
def get_bookable_dates(service_id):
    try:
        # Fetch the service to get its available dates
        service = mongo.db.services.find_one({'_id': ObjectId(service_id)})
        if not service:
            return jsonify({"message": "Service not found"}), 404
        
        bookable_dates = service.get('available_dates', [])

        return jsonify({"bookable_dates": bookable_dates}), 200
    except Exception as e:
        logger.error(f"Failed to get bookable dates for service {service_id}: {e}")
        abort(500, "Internal Server Error")


@app.route('/api/appointments/<appointment_id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(appointment_id):
    current_user = get_jwt_identity()

    appointment = mongo.db.appointments.find_one({'_id': ObjectId(appointment_id)})
    if not appointment:
        return jsonify({"msg": "Appointment not found"}), 404

    if appointment['user'] != current_user:
        return jsonify({"msg": "Unauthorized to delete this appointment"}), 403

    # Delete the appointment
    mongo.db.appointments.delete_one({'_id': ObjectId(appointment_id)})

    return jsonify({"msg": "Appointment deleted successfully"}), 200
