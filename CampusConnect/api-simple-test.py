import requests
from requests.exceptions import HTTPError

BASE_URL = "http://localhost:4105"

def register_user(username, password):
    url = f"{BASE_URL}/api/register"
    payload = {"username": username, "password": password}
    response = requests.post(url, json=payload)
    if response.status_code < 400:
        print("Register:", response.json())

def login(username, password):
    url = f"{BASE_URL}/api/login"
    payload = {"username": username, "password": password}
    response = requests.post(url, json=payload)
    if response.status_code < 400:
        print("Login:", response.json())
        return response.json().get("access_token")
    else:
        return None

def create_product(access_token, user, description):
    url = f"{BASE_URL}/api/products"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"user": user, "description": description}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code < 400:
        print("Create Product:", response.json())

def create_service(access_token, user, description):
    url = f"{BASE_URL}/api/services"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"user": user, "description": description}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code < 400:
        print("Create Service:", response.json())

def get_products():
    response = requests.get(f"{BASE_URL}/api/products")
    if response.status_code < 400:
        print(f"Get Products status: {response.status_code}, {response.text}")

def get_services():
    response = requests.get(f"{BASE_URL}/api/services")
    if response.status_code < 400:
        print(f"Get Services status: {response.status_code}, {response.text}")
    

if __name__ == "__main__":
    username = "testuser"
    password = "password"


    register_user(username, password)
  
    access_token = login(username, password)
    print(f"Access token: {access_token}")
    
    create_product(access_token, username, "A new test product")
    create_service(access_token, username, "A new test service")
    create_service(access_token, "wrong user", "Another test service")
    
    get_products()
    get_services()
    
