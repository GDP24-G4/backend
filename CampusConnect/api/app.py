import logging
from flask import Flask, request, abort
from flask_pymongo import PyMongo
from bson import json_util, ObjectId
import pymongo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://mongo:27017/campus-connect?serverSelectionTimeoutMS=1000'  # 1000 milliseconds timeout
mongo = PyMongo(app)

@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url} - Data: {request.json}")

def handle_db_call(call):
    try:
        return call()
    except pymongo.errors.ServerSelectionTimeoutError:
        logger.error("Database connection timeout")
        abort(503, "Database connection timeout")

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
        product = handle_db_call(lambda: mongo.db.products.find_one_or_404({'_id': ObjectId(product_id)}))
        return json_util.dumps(product)
    except Exception as e:
        logger.error(f"Failed to retrieve product {product_id}: {e}")
        abort(500, "Internal Server Error")

@app.route('/api/products', methods=['POST'])
def create_product():
    try:
        product_data = request.json
        if not all(key in product_data for key in ['user', 'description']):
            abort(400, "Missing required fields for product listing")
        product_id = handle_db_call(lambda: mongo.db.products.insert_one(product_data).inserted_id)
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
        service = handle_db_call(lambda: mongo.db.services.find_one_or_404({'_id': ObjectId(service_id)}))
        return json_util.dumps(service)
    except Exception as e:
        logger.error(f"Failed to retrieve service {service_id}: {e}")
        abort(500, "Internal Server Error")

@app.route('/api/services', methods=['POST'])
def create_service():
    try:
        service_data = request.json
        if not all(key in service_data for key in ['user', 'description']):
            abort(400, "Missing required fields for service")
        service_id = handle_db_call(lambda: mongo.db.services.insert_one(service_data).inserted_id)
        return json_util.dumps({"message": "Service created successfully", "service_id": str(service_id)}), 201
    except Exception as e:
        logger.error(f"Failed to create service: {e}")
        abort(500, "Internal Server Error")

@app.route('/api/appointments/<service_id>', methods=['GET'])
def get_appointments_for_service(service_id):
    try:
        appointments = handle_db_call(lambda: list(mongo.db.appointments.find({'service_id': service_id})))
        return json_util.dumps(appointments)

    except Exception as e:
        logger.error(f"Failed to retrieve appointments for service {service_id}: {e}")
        abort(500, "Internal Server Error")

@app.route('/api/appointments', methods=['POST'])
def book_appointment():
    try:
        appointment_data = request.json
        if not all(key in appointment_data for key in ['service_id', 'timeslot', 'user']):
            abort(400, "Missing required fields for appointment")
        
        service = handle_db_call(lambda: mongo.db.services.find_one({'_id': ObjectId(appointment_data['service_id'])}))

        if not service:
            abort(404, "Service not found")
        
        existing_appointment = handle_db_call(lambda: mongo.db.appointments.find_one({
            'service_id': appointment_data['service_id'],
            'timeslot': appointment_data['timeslot']
        }))

        if existing_appointment:
            abort(409, "Appointment already booked for this timeslot")
        
        appointment_id = handle_db_call(lambda: mongo.db.appointments.insert_one(appointment_data).inserted_id)
        return json_util.dumps({"message": "Appointment booked successfully", "appointment_id": str(appointment_id)}), 200
    except Exception as e:
        logger.error(f"Failed to book appointment: {e}")
        abort(500, "Internal Server Error")
