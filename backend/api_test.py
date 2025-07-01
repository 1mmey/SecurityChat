import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

# --- Helper Functions ---

def register_user(username, email, password):
    """Helper to register a user."""
    url = f"{BASE_URL}/users/"
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "public_key": f"key_for_{username}"
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(user_data), headers=headers)
    return response

def login_user(username, password):
    """Helper to log in a user and get a token."""
    url = f"{BASE_URL}/token"
    login_data = {"username": username, "password": password}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=login_data, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def add_contact(token, friend_id):
    """Helper to add a contact."""
    url = f"{BASE_URL}/me/contacts/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"friend_id": friend_id}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response

def get_contacts(token):
    """Helper to get the contacts list."""
    url = f"{BASE_URL}/me/contacts/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response

# --- Main Test Execution ---

if __name__ == "__main__":
    # Define two users
    user1_name = f"user1_{int(time.time())}"
    user2_name = f"user2_{int(time.time())}"
    user1_email = f"{user1_name}@example.com"
    user2_email = f"{user2_name}@example.com"
    password = "password123"

    # 1. Register User 1
    print(f"--- 1. Registering {user1_name} ---")
    resp1 = register_user(user1_name, user1_email, password)
    print(f"Status: {resp1.status_code}, Response: {resp1.text}")
    assert resp1.status_code == 200, "Failed to register user1"
    user1_id = resp1.json()["id"]
    print(f"✅ {user1_name} registered with ID: {user1_id}\n")

    # 2. Register User 2
    print(f"--- 2. Registering {user2_name} ---")
    resp2 = register_user(user2_name, user2_email, password)
    print(f"Status: {resp2.status_code}, Response: {resp2.text}")
    assert resp2.status_code == 200, "Failed to register user2"
    user2_id = resp2.json()["id"]
    print(f"✅ {user2_name} registered with ID: {user2_id}\n")

    # 3. User 1 logs in
    print(f"--- 3. Logging in as {user1_name} ---")
    token1 = login_user(user1_name, password)
    print(f"Token received: {'Yes' if token1 else 'No'}")
    assert token1 is not None, "Failed to log in as user1"
    print(f"✅ {user1_name} logged in successfully\n")

    # 4. User 1 adds User 2 as a contact
    print(f"--- 4. {user1_name} adds {user2_name} as a contact ---")
    resp_add = add_contact(token1, user2_id)
    print(f"Status: {resp_add.status_code}, Response: {resp_add.text}")
    assert resp_add.status_code == 200, "Failed to add contact"
    print(f"✅ {user1_name} successfully added {user2_name} as a contact!\n")

    # 5. User 1 gets their contact list
    print(f"--- 5. {user1_name} gets their contact list ---")
    resp_get = get_contacts(token1)
    print(f"Status: {resp_get.status_code}, Response: {resp_get.text}")
    assert resp_get.status_code == 200, "Failed to get contact list"
    
    contacts_list = resp_get.json()
    assert isinstance(contacts_list, list), "Contacts response is not a list"
    assert len(contacts_list) > 0, "Contacts list is empty"
    
    friend_ids = [c["friend_id"] for c in contacts_list]
    assert user2_id in friend_ids, "User2 is not in the contact list"
    
    print(f"✅ {user1_name}'s contact list correctly contains {user2_name}!")

    print("\n🎉 All contact management tests passed! 🎉") 