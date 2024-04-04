import requests
import subprocess
import random
import time

API_BASE_URL = "http://localhost:4105"

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

def start_docker():
    print("Starting Docker container...")
    run_command("docker-compose up -d")
    print("Sleeping for 5 seconds for the server to start...")
    time.sleep(5)

def stop_docker():
    print("Stopping Docker container...")
    run_command("docker-compose down")
    print("--------------------------------------------------------")

def test_appointments_and_bookings():
    print("Testing Product Search...")

    # Register and login a user
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = response.json().get("access_token")

    # Create dummy products
    product_data = {"user": "testuser", "description": "Dummy Product 1", "price": 10, "quantity": 100}
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE_URL}/api/products", json=product_data, headers=headers)
    assert response.status_code == 201, "\033[91mFailed to create dummy product.\033[0m"
    product_id = response.json().get("product_id")

    service_data = {
        "user": "testuser",
        "description": "Test Service",
        "price": 100,
        "available_dates": ["2024-04-01T09:00:00", "2024-04-08T09:00:00"]
    }

    response = requests.post(f"{API_BASE_URL}/api/services", json=service_data, headers=headers)
    assert response.status_code == 201, "\033[91mFailed to create test service.\033[0m"
    service_id = response.json()["service_id"]

    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser1", "password": "password"})
    assert response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser1", "password": "password"})
    assert response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = response.json().get("access_token")

    headers = {"Authorization": f"Bearer {token}"}


    # Book an appointment with valid data
    appointment_data = {
        "user": "testuser1",
        "service_id": service_id,
        "timeslot": "2024-04-01T09:00:00"
    }

    response = requests.post(f"{API_BASE_URL}/api/appointments", json=appointment_data, headers=headers)
    assert response.status_code == 200, "\033[91mFailed to book appointment.\033[0m"


    response = requests.post(f"{API_BASE_URL}/api/purchase_product/{product_id}", headers=headers)
    assert response.status_code == 200, "\033[91mFailed: Purchase of product.\033[0m"


    response = requests.get(f"{API_BASE_URL}/api/user/appointments_and_bookings", headers=headers)
    assert response.status_code == 200, "\033[91mFailed: to get appointments and bookings.\033[0m"
    data = response.json()
    assert len(data['user_bookings']) == 1
    assert len(data['user_appointments']) == 1
    print("Passed: User purchases and bookings.")

def test_product_search():
    print("Testing Product Search...")

    # Register and login a user
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = response.json().get("access_token")

    # Create dummy products
    product_data = [
        {"user": "testuser", "description": "Dummy Product 1", "price": 10, "quantity": 100},
        {"user": "testuser", "description": "Dummy Product 2", "price": 15, "quantity": 50},
        {"user": "testuser", "description": "Dummy Product 3", "price": 20, "quantity": 200},
        {"user": "testuser", "description": "Birds in the shky", "price": 20, "quantity": 200}
    ]
    headers = {"Authorization": f"Bearer {token}"}
    for data in product_data:
        response = requests.post(f"{API_BASE_URL}/api/products", json=data, headers=headers)
        assert response.status_code == 201, "\033[91mFailed to create dummy product.\033[0m"


        
    # Test product search with a partial title
    response = requests.get(f"{API_BASE_URL}/api/products/search?title=dummy")
    print(response)
    assert response.status_code == 200, "\033[91mFailed: Product search with partial title test.\033[0m"
    data = response.json()
    print(data)
    assert len(data['products']) == 3
    print("Passed: Product Search tests.")



def test_health_check():
    print("Testing Health Check Endpoint...")
    response = requests.get(f"{API_BASE_URL}/health-check")
    
    assert response.status_code == 200, "\033[91mFailed: Status code check.\033[0m"
    assert response.text == "OK", "\033[91mFailed: Body content check.\033[0m"
    print("Passed: Health Check test.")

def test_register():
    print("Testing Registration...")
    username = f"testuser_{random.randint(1000, 9999)}"
    password = "password"

    # Test missing fields
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "", "password": "password"})
    assert response.status_code == 400, "\033[91mFailed: Registration with missing fields test.\033[0m"

    # Test successful registration
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": username, "password": "password"})
    assert response.status_code == 201, "\033[91mFailed: Successful registration test.\033[0m"

    # Test duplicate username
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": username, "password": password})
    assert response.status_code == 409, "\033[91mFailed: Duplicate username test.\033[0m"
    print("Passed: Registration tests.")

def test_login():
    print("Testing Login...")
    username = f"testuser_{random.randint(1000, 9999)}"
    password = "password"

    # Register a new user
    requests.post(f"{API_BASE_URL}/api/register", json={"username": username, "password": password})

    # Attempt to log in with the new user
    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": username, "password": password})
    data = response.json()

    assert response.status_code == 200, "\033[91mFailed: Login status code check.\033[0m"
    assert 'access_token' in data, "\033[91mFailed: Login access token check.\033[0m"
    print("Passed: Login test.")

def test_check_username():
    print("Testing Check Username Endpoint...")
    username = f"testuser_{random.randint(1000, 9999)}"

    # Check availability of a non-existing username
    response = requests.get(f"{API_BASE_URL}/api/check_username?username={username}")
    data = response.json()

    assert response.status_code == 200, "\033[91mFailed: Check Username status code check.\033[0m"
    assert data['available'] == True, "\033[91mFailed: Check Username for non-existing username.\033[0m"
    print("Passed: Check Username test.")


def test_check_existing_username():
    print("Testing Check Existing Username Endpoint...")

    # Register a user with a specific username
    username = f"testuser_{random.randint(1000, 9999)}"
    register_response = requests.post(f"{API_BASE_URL}/api/register", json={"username": username, "password": "password"})

    if register_response.status_code == 201:
        # Check availability of the registered username
        response = requests.get(f"{API_BASE_URL}/api/check_username?username={username}")
        data = response.json()

        assert response.status_code == 200, "\033[91mFailed: Check Existing Username status code check.\033[0m"
        assert data['available'] == False, "\033[91mFailed: Check Existing Username for existing username.\033[0m"
        print("Passed: Check Existing Username test.")
    else:
        print(f"\033[91mFailed to register user '{username}'. Test skipped.\033[0m")


def test_get_products():
    print("Testing Get Products Endpoint with Dummy Products...")

    # Register and login a user
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = response.json().get("access_token")

    # Create dummy products
    product_data = [
        {"user": "testuser", "description": "Dummy Product 1", "price": 10, "quantity": 100},
        {"user": "testuser", "description": "Dummy Product 2", "price": 15, "quantity": 50},
        {"user": "testuser", "description": "Dummy Product 3", "price": 20, "quantity": 200}
    ]
    headers = {"Authorization": f"Bearer {token}"}
    for data in product_data:
        response = requests.post(f"{API_BASE_URL}/api/products", json=data, headers=headers)
        assert response.status_code == 201, "\033[91mFailed to create dummy product.\033[0m"

    # Attempt to get products
    response = requests.get(f"{API_BASE_URL}/api/products")
    assert response.status_code == 200, "\033[91mFailed: Get Products status code check.\033[0m"

    products = response.json()
    assert len(products) >= 3, "\033[91mFailed: Dummy products not found in response.\033[0m"

    print("Passed: Get Products test with Dummy Products.")


def test_get_product():
    print("Testing Get Product Endpoint...")

    # Register and login a user
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = response.json().get("access_token")

    # Create a dummy product
    headers = {"Authorization": f"Bearer {token}"}
    product_data = {"user": "testuser", "description": "Dummy Product", "price": 10, "quantity": 100}
    response = requests.post(f"{API_BASE_URL}/api/products", json=product_data, headers=headers)
    assert response.status_code == 201, "\033[91mFailed to create dummy product.\033[0m"
    product_id = response.json().get("product_id")

    # Attempt to get the created product
    response = requests.get(f"{API_BASE_URL}/api/products/{product_id}")
    assert response.status_code == 200, "\033[91mFailed: Get Product status code check.\033[0m"

    product = response.json()
    assert product["_id"]["$oid"] == product_id, "\033[91mFailed: Product ID mismatch.\033[0m"

    print("Passed: Get Product test.")


def test_purchase_product():
    print("Testing Purchase Product Endpoint...")

    # Register seller
    seller_username = "seller"
    seller_password = "seller_password"
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": seller_username, "password": seller_password})
    assert response.status_code == 201, "\033[91mFailed to register seller.\033[0m"

    # Login seller
    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": seller_username, "password": seller_password})
    assert response.status_code == 200, "\033[91mFailed to login seller.\033[0m"
    seller_token = response.json().get("access_token")

    # Create product
    product_description = "Test Product"
    product_price = 10
    product_quantity = 5
    product_data = {"user": seller_username, "description": product_description, "price": product_price, "quantity": product_quantity}
    response = requests.post(f"{API_BASE_URL}/api/products", json=product_data, headers={"Authorization": f"Bearer {seller_token}"})
    assert response.status_code == 201, "\033[91mFailed to create product.\033[0m"
    product_id = response.json().get("product_id")

    # Register buyer
    buyer_username = "buyer"
    buyer_password = "buyer_password"
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": buyer_username, "password": buyer_password})
    assert response.status_code == 201, "\033[91mFailed to register buyer.\033[0m"

    # Login buyer
    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": buyer_username, "password": buyer_password})
    assert response.status_code == 200, "\033[91mFailed to login buyer.\033[0m"
    buyer_token = response.json().get("access_token")

    # Test purchase scenarios
    response = requests.post(f"{API_BASE_URL}/api/purchase_product/{product_id}", headers={"Authorization": f"Bearer {buyer_token}"})
    assert response.status_code == 200, "\033[91mFailed: Purchase of product.\033[0m"

    # Attempt to purchase own product
    response = requests.post(f"{API_BASE_URL}/api/purchase_product/{product_id}", headers={"Authorization": f"Bearer {seller_token}"})
    assert response.status_code == 403, "\033[91mFailed: Seller purchasing own product.\033[0m"

    # Attempt to purchase sold out product
    for _ in range(product_quantity-1):
        response = requests.post(f"{API_BASE_URL}/api/purchase_product/{product_id}", headers={"Authorization": f"Bearer {buyer_token}"})
        assert response.status_code == 200, "\033[91mFailed: Purchase of product.\033[0m"
    response = requests.post(f"{API_BASE_URL}/api/purchase_product/{product_id}", headers={"Authorization": f"Bearer {buyer_token}"})
    assert response.status_code == 409, "\033[91mFailed: Purchase of sold out product.\033[0m"

    print("Passed: Purchase Product test.")


def test_product_sold_out():
    print("Testing Product Sold Out Endpoint...")

    # Register seller
    seller_username = "seller"
    seller_password = "seller_password"
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": seller_username, "password": seller_password})
    assert response.status_code == 201, "\033[91mFailed to register seller.\033[0m"

    # Login seller
    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": seller_username, "password": seller_password})
    assert response.status_code == 200, "\033[91mFailed to login seller.\033[0m"
    seller_token = response.json().get("access_token")

    # Create product
    product_description = "Test Product"
    product_price = 10
    product_quantity = 2  # Limited quantity
    product_data = {"user": seller_username, "description": product_description, "price": product_price, "quantity": product_quantity}
    response = requests.post(f"{API_BASE_URL}/api/products", json=product_data, headers={"Authorization": f"Bearer {seller_token}"})
    assert response.status_code == 201, "\033[91mFailed to create product.\033[0m"
    product_id = response.json().get("product_id")

    # Register buyer
    buyer_username = "buyer"
    buyer_password = "buyer_password"
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": buyer_username, "password": buyer_password})
    assert response.status_code == 201, "\033[91mFailed to register buyer.\033[0m"

    # Login buyer
    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": buyer_username, "password": buyer_password})
    assert response.status_code == 200, "\033[91mFailed to login buyer.\033[0m"
    buyer_token = response.json().get("access_token")

    # Purchase all available products to make it sold out
    for _ in range(product_quantity):
        response = requests.post(f"{API_BASE_URL}/api/purchase_product/{product_id}", headers={"Authorization": f"Bearer {buyer_token}"})
        assert response.status_code == 200, "\033[91mFailed: Purchase of product.\033[0m"

    # Check if product is sold out
    response = requests.get(f"{API_BASE_URL}/api/products/{product_id}/is_sold_out")
    assert response.status_code == 200, "\033[91mFailed to check if product is sold out.\033[0m"
    assert response.json().get("is_sold_out") == True, "\033[91mProduct is not marked as sold out.\033[0m"

    print("Passed: Product Sold Out test.")


def test_delete_product():
    print("Testing Delete Product Endpoint...")

    # Register user
    username = "test_user"
    password = "test_password"
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": username, "password": password})
    assert response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    # Login user
    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": username, "password": password})
    assert response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    access_token = response.json().get("access_token")

    # Create product
    product_data = {"user": username, "description": "Test Product", "price": 10, "quantity": 1}
    response = requests.post(f"{API_BASE_URL}/api/products", json=product_data, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 201, "\033[91mFailed to create product.\033[0m"
    product_id = response.json().get("product_id")
    

    # Delete product
    response = requests.delete(f"{API_BASE_URL}/api/products/{product_id}", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200, "\033[91mFailed to delete product.\033[0m"

    # Attempt to retrieve deleted product
    response = requests.get(f"{API_BASE_URL}/api/products/{product_id}")
    assert response.status_code == 500, "\033[91mDeleted product still exists.\033[0m"

    print("Passed: Delete Product test.")

def test_get_services():
    print("Testing Get Services Endpoint...")

    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = response.json().get("access_token")

    # Create a dummy product
    headers = {"Authorization": f"Bearer {token}"}

    # Create test services
    service_ids = []
    for i in range(3):
        service_data = {
            "user": "testuser",
            "description": f"Test Service {i}",
            "price": 10 * (i + 1),
            "available_dates": [f"2024-04-{i+1}"]
        }
        response = requests.post(f"{API_BASE_URL}/api/services", json=service_data, headers=headers)
        assert response.status_code == 201, "\033[91mFailed to create test services.\033[0m"
        service_ids.append(response.json()["service_id"])

    # Retrieve services
    response = requests.get(f"{API_BASE_URL}/api/services")
    assert response.status_code == 200, "\033[91mFailed to retrieve services.\033[0m"
    services = response.json()

    # Check if all test services are in the response
    for service_id in service_ids:
        assert any(service["_id"]["$oid"]  == service_id for service in services), f"\033[91mService with ID {service_id} not found.\033[0m"

    print("Passed: Get Services test.")

def test_get_service():
    print("Testing Get Service Endpoint...")

    # Register and login a user to get the JWT token
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = response.json().get("access_token")

    # Create a dummy service
    headers = {"Authorization": f"Bearer {token}"}
    service_data = {
        "user": "testuser",
        "description": "Test Service",
        "price": 100,
        "available_dates": ["2024-04-01"]
    }
    response = requests.post(f"{API_BASE_URL}/api/services", json=service_data, headers=headers)
    assert response.status_code == 201, "\033[91mFailed to create test service.\033[0m"
    service_id = response.json()["service_id"]

    # Retrieve the created service
    response = requests.get(f"{API_BASE_URL}/api/services/{service_id}")
    assert response.status_code == 200, "\033[91mFailed to retrieve service.\033[0m"
    service = response.json()

    # Check if the retrieved service matches the created service
    assert service["_id"]["$oid"] == service_id, f"\033[91mRetrieved service ID does not match the created service ID.\033[0m"

    print("Passed: Get Service test.")


def test_book_appointment():
    print("Testing Book Appointment Endpoint...")

    # Register and login a user to get the JWT token
    response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = response.json().get("access_token")

    # Create a dummy service
    headers = {"Authorization": f"Bearer {token}"}
    service_data = {
        "user": "testuser",
        "description": "Test Service",
        "price": 100,
        "available_dates": ["2024-04-01T09:00:00", "2024-04-08T09:00:00"]
    }
    response = requests.post(f"{API_BASE_URL}/api/services", json=service_data, headers=headers)
    assert response.status_code == 201, "\033[91mFailed to create test service.\033[0m"
    service_id = response.json()["service_id"]

    # Book an appointment with valid data
    appointment_data = {
        "user": "testuser",
        "service_id": service_id,
        "timeslot": "2024-04-01T09:00:00"
    }
    response = requests.post(f"{API_BASE_URL}/api/appointments", json=appointment_data, headers=headers)
    assert response.status_code == 200, "\033[91mFailed to book appointment.\033[0m"

    # Attempt to book the same appointment again (should fail)
    response = requests.post(f"{API_BASE_URL}/api/appointments", json=appointment_data, headers=headers)
    assert response.status_code == 409, "\033[91mBooking same appointment again should fail but it did not.\033[0m"

    # Book an appointment with invalid service ID
    appointment_data["service_id"] = "aaaae375d4eb9c7490130f0f"
    response = requests.post(f"{API_BASE_URL}/api/appointments", json=appointment_data, headers=headers)
    assert response.status_code == 404, "\033[91mBooking appointment with invalid service ID should fail but it did not.\033[0m"

    # Book an appointment with invalid timeslot
    appointment_data["service_id"] = service_id
    appointment_data["timeslot"] = "2024-04-02T09:00:00"  # Invalid timeslot
    response = requests.post(f"{API_BASE_URL}/api/appointments", json=appointment_data, headers=headers)
    assert response.status_code == 409, "\033[91mBooking appointment with invalid timeslot should fail but it did not.\033[0m"

    print("Passed: Book Appointment test.")


def test_get_appointments_for_service():
    print("Testing Get Appointments for Service Endpoint...")

    # Register a user
    register_response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert register_response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    # Login the registered user to obtain an access token
    login_response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert login_response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = login_response.json().get("access_token")

    # Create a test service
    service_data = {
        "user": "testuser",
        "description": "Test Service",
        "price": 50,
        "available_dates": ["2024-04-01T09:00:00", "2024-04-02T09:00:00"]
    }
    headers = {"Authorization": f"Bearer {token}"}
    create_service_response = requests.post(f"{API_BASE_URL}/api/services", json=service_data, headers=headers)
    assert create_service_response.status_code == 201, "\033[91mFailed to create test service.\033[0m"
    service_id = create_service_response.json().get("service_id")

    # Book an appointment for the test service
    appointment_data = {
        "service_id": service_id,
        "timeslot": "2024-04-01T09:00:00",  # Assuming this timeslot is available for booking
        "user": "testuser"
    }
    book_appointment_response = requests.post(f"{API_BASE_URL}/api/appointments", json=appointment_data, headers=headers)
    assert book_appointment_response.status_code == 200, "\033[91mFailed to book appointment for test service.\033[0m"

    # Retrieve appointments for the test service
    get_appointments_response = requests.get(f"{API_BASE_URL}/api/appointments/{service_id}")
    assert get_appointments_response.status_code == 200, "\033[91mFailed to retrieve appointments for test service.\033[0m"
    appointments = get_appointments_response.json()

    # Check if the booked appointment is in the response
    assert len(appointments) == 1, "\033[91mExpected 1 appointment, but received a different number.\033[0m"

    print("Passed: Get Appointments for Service test.")


def test_get_bookable_dates():
    print("Testing Get Bookable Dates Endpoint...")

    # Register a user
    register_response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert register_response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    # Login the registered user to obtain an access token
    login_response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert login_response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = login_response.json().get("access_token")

    # Create a test service with available dates
    service_data = {
        "user": "testuser",
        "description": "Test Service",
        "price": 50,
        "available_dates": ["2024-04-01T09:00:00", "2024-04-02T09:00:00", "2024-04-03T09:00:00"]
    }
    headers = {"Authorization": f"Bearer {token}"}
    create_service_response = requests.post(f"{API_BASE_URL}/api/services", json=service_data, headers=headers)
    assert create_service_response.status_code == 201, "\033[91mFailed to create test service.\033[0m"
    service_id = create_service_response.json().get("service_id")

    # Book an appointment for one of the available dates
    appointment_data = {
        "service_id": service_id,
        "timeslot": "2024-04-01T09:00:00",  # Assuming this timeslot is available for booking
        "user": "testuser"
    }
    book_appointment_response = requests.post(f"{API_BASE_URL}/api/appointments", json=appointment_data, headers=headers)
    assert book_appointment_response.status_code == 200, "\033[91mFailed to book appointment for test service.\033[0m"

    # Retrieve bookable dates for the test service
    get_bookable_dates_response = requests.get(f"{API_BASE_URL}/api/bookable_dates/{service_id}")
    assert get_bookable_dates_response.status_code == 200, "\033[91mFailed to retrieve bookable dates for test service.\033[0m"
    bookable_dates = get_bookable_dates_response.json().get("bookable_dates")

    # Check if the booked date is not included in the bookable dates
    assert "2024-04-01T09:00:00" not in bookable_dates, "\033[91mBooked date should not be included in bookable dates.\033[0m"

    print("Passed: Get Bookable Dates test.")

def test_delete_service():
    print("Testing Delete Service Endpoint...")

    # Register a user
    register_response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert register_response.status_code == 201, "\033[91mFailed to register user.\033[0m"

    # Login the registered user to obtain an access token
    login_response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert login_response.status_code == 200, "\033[91mFailed to login user.\033[0m"
    token = login_response.json().get("access_token")

    # Create a test service
    service_data = {
        "user": "testuser",
        "description": "Test Service",
        "price": 50,
        "available_dates": ["2024-04-01T09:00:00", "2024-04-02T09:00:00", "2024-04-03T09:00:00"]
    }
    headers = {"Authorization": f"Bearer {token}"}
    create_service_response = requests.post(f"{API_BASE_URL}/api/services", json=service_data, headers=headers)
    assert create_service_response.status_code == 201, "\033[91mFailed to create test service.\033[0m"
    service_id = create_service_response.json().get("service_id")

    # Create a test appointment for the service
    appointment_data = {
        "user": "testuser",
        "service_id": service_id,
        "timeslot": "2024-04-01T09:00:00"
    }
    create_appointment_response = requests.post(f"{API_BASE_URL}/api/appointments", json=appointment_data, headers=headers)
    assert create_appointment_response.status_code == 200, "\033[91mFailed to create test appointment.\033[0m"
    appointment_id = create_appointment_response.json().get("appointment_id")

    # Delete the test service
    delete_service_response = requests.delete(f"{API_BASE_URL}/api/services/{service_id}", headers=headers)
    assert delete_service_response.status_code == 200, "\033[91mFailed to delete test service.\033[0m"

    # Verify that the service is deleted
    get_service_response = requests.get(f"{API_BASE_URL}/api/services/{service_id}")
    assert get_service_response.status_code == 500, "\033[91mService still exists after deletion.\033[0m"

    # Verify that the appointment associated with the service is deleted
    get_appointment_response = requests.get(f"{API_BASE_URL}/api/appointments/{service_id}")
    assert len(get_appointment_response.json()) == 0, "\033[91mAppointment still exists after service deletion.\033[0m"


    print("Passed: Delete Service test.")

def test_delete_appointment():
    print("Testing Delete Appointment Endpoint...")

    # Register a test user
    register_response = requests.post(f"{API_BASE_URL}/api/register", json={"username": "testuser", "password": "password"})
    assert register_response.status_code == 201, "Failed to register user."
    
    # Log in the test user and obtain the token
    login_response = requests.post(f"{API_BASE_URL}/api/login", json={"username": "testuser", "password": "password"})
    assert login_response.status_code == 200, "Failed to login user."
    token = login_response.json().get("access_token")

    # Create a test service
    service_data = {
        "user": "testuser",
        "description": "Test Service",
        "price": 50,
        "available_dates": ["2024-04-01T09:00:00", "2024-04-02T10:00:00"]
    }
    headers = {"Authorization": f"Bearer {token}"}
    create_service_response = requests.post(f"{API_BASE_URL}/api/services", json=service_data, headers=headers)
    assert create_service_response.status_code == 201, "Failed to create test service."
    service_id = create_service_response.json().get("service_id")

    # Book an appointment for the test service
    appointment_data = {
        "user": "testuser",
        "service_id": service_id,
        "timeslot": "2024-04-01T09:00:00"
    }
    book_appointment_response = requests.post(f"{API_BASE_URL}/api/appointments", json=appointment_data, headers=headers)
    assert book_appointment_response.status_code == 200, "Failed to book test appointment."
    appointment_id = book_appointment_response.json().get("appointment_id")

    # Attempt to delete the appointment
    delete_response = requests.delete(f"{API_BASE_URL}/api/appointments/{appointment_id}", headers=headers)
    assert delete_response.status_code == 200, "Failed to delete appointment."

    print("Passed: Delete Appointment test.")

# Main script
tests = [   ("Test appointments and bookings", test_appointments_and_bookings),
            ("Test search", test_product_search),
            ("Test register", test_register), 
            ("Test login", test_login), 
            ("Test check username", test_check_username),
            ("Test check existing username", test_check_existing_username),
            ('Test delete appointment', test_delete_appointment),
            ('Test delete service', test_delete_service),
            ('Test get bookable dates', test_get_bookable_dates),
            ('Test get appointments', test_get_appointments_for_service),
            ('Test book appointment', test_book_appointment), 
            ('Test get service', test_get_service),
            ('Test get services', test_get_services), 
            ('Test delete product', test_delete_product),
            ('Test product sold out', test_product_sold_out), 
            ('Test purchase product', test_purchase_product) ,
            ('Test get product', test_get_product), 
            ("Test get products", test_get_products), 
            ("Test health Check", test_health_check)
                                                            ]
results = []

for name, test_func in tests:
    stop_docker()
    start_docker()
    try:
        test_func()
        results.append((name, "Passed"))
        print(f"\033[92mOK: {name}\033[0m")
    except AssertionError as e:
        results.append((name, e.args[0]))
        print(f"\033[91mFailure: {name}\033[0m")

stop_docker()

print("\nTest Report:")
for test_name, result in results:
    color = "\033[91m" if "Failed" in result else "\033[92m"
    print(f"{test_name}: {color}{result}\033[0m")
