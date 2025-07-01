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

def update_connection_info(token, port):
    """Helper to update connection info (heartbeat)."""
    url = f"{BASE_URL}/me/connection-info"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"port": port}
    response = requests.put(url, data=json.dumps(data), headers=headers)
    return response

def get_connection_info(token, username):
    """Helper to get another user's connection info."""
    url = f"{BASE_URL}/users/{username}/connection-info"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response

def logout_user(token):
    """Helper to log out the current user."""
    url = f"{BASE_URL}/logout"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    return response

def send_offline_message(token, recipient_username, content):
    """Helper to send an offline message."""
    url = f"{BASE_URL}/messages/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"recipient_username": recipient_username, "encrypted_content": content}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response

def get_offline_messages(token):
    """Helper to get offline messages for the current user."""
    url = f"{BASE_URL}/messages/"
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


    print("\n--- Starting Connection and Status Tests ---")

    # 6. User 2 logs in to become online
    print(f"--- 6. Logging in as {user2_name} to be online ---")
    token2 = login_user(user2_name, password)
    assert token2 is not None, "Failed to log in as user2"
    print(f"✅ {user2_name} is now online.\n")
    
    # 7. User 1 sends a heartbeat and updates port
    print(f"--- 7. {user1_name} sends heartbeat (updates port to 9999) ---")
    resp_heartbeat = update_connection_info(token1, 9999)
    print(f"Status: {resp_heartbeat.status_code}, Response: {resp_heartbeat.text}")
    assert resp_heartbeat.status_code == 200, "Failed to send heartbeat"
    print(f"✅ {user1_name} heartbeat successful.\n")

    # 8. User 1 gets User 2's connection info
    print(f"--- 8. {user1_name} gets {user2_name}'s connection info ---")
    resp_conn_info = get_connection_info(token1, user2_name)
    print(f"Status: {resp_conn_info.status_code}, Response: {resp_conn_info.text}")
    assert resp_conn_info.status_code == 200, "Failed to get connection info for user2"
    conn_info = resp_conn_info.json()
    assert "public_key" in conn_info and "ip_address" in conn_info
    print(f"✅ Successfully retrieved connection info for {user2_name}.\n")
    
    # 9. User 1 logs out
    print(f"--- 9. {user1_name} logs out ---")
    resp_logout = logout_user(token1)
    print(f"Status: {resp_logout.status_code}, Response: {resp_logout.text}")
    assert resp_logout.status_code == 200, "Failed to log out"
    print(f"✅ {user1_name} logged out successfully.\n")

    # 10. User 2 tries to get User 1's connection info (should fail)
    print(f"--- 10. {user2_name} tries to get {user1_name}'s info (should fail as user1 is offline) ---")
    resp_conn_fail = get_connection_info(token2, user1_name)
    print(f"Status: {resp_conn_fail.status_code}, Response: {resp_conn_fail.text}")
    assert resp_conn_fail.status_code == 404, "Should not get info for an offline user"
    print(f"✅ Correctly failed to get info for offline user {user1_name}.")

    print("\n🎉 All connection and status tests passed! 🎉")

    print("\n--- Starting Offline Message Tests ---")

    # 11. User 2 sends an offline message to User 1 (who is offline)
    print(f"--- 11. {user2_name} sends an offline message to {user1_name} ---")
    message_content = "SGVsbG8gd29ybGQh" # "Hello world!" in Base64
    resp_send_msg = send_offline_message(token2, user1_name, message_content)
    print(f"Status: {resp_send_msg.status_code}, Response: {resp_send_msg.text}")
    assert resp_send_msg.status_code == 200, "Failed to send offline message"
    print(f"✅ {user2_name} sent message to {user1_name} successfully.\n")

    # 12. User 1 logs back in
    print(f"--- 12. {user1_name} logs back in ---")
    token1_new = login_user(user1_name, password)
    assert token1_new is not None, "Failed to log in as user1 again"
    print(f"✅ {user1_name} is online again.\n")

    # 13. User 1 fetches their offline messages
    print(f"--- 13. {user1_name} fetches offline messages ---")
    resp_get_msgs = get_offline_messages(token1_new)
    print(f"Status: {resp_get_msgs.status_code}, Response: {resp_get_msgs.text}")
    assert resp_get_msgs.status_code == 200, "Failed to get offline messages"
    messages = resp_get_msgs.json()
    assert len(messages) == 1, "Should have received one message"
    assert messages[0]["encrypted_content"] == message_content, "Message content mismatch"
    assert messages[0]["sender_id"] == user2_id, "Sender ID mismatch"
    print(f"✅ {user1_name} correctly received the message from {user2_name}.\n")

    # 14. User 1 fetches messages again (should be empty)
    print(f"--- 14. {user1_name} fetches again, should be empty ---")
    resp_get_again = get_offline_messages(token1_new)
    print(f"Status: {resp_get_again.status_code}, Response: {resp_get_again.text}")
    assert resp_get_again.status_code == 200, "Second fetch failed"
    messages_again = resp_get_again.json()
    assert len(messages_again) == 0, "Messages should be empty after first fetch"
    print("✅ Correctly received no new messages.")

    print("\n🎉 All offline message tests passed! 🎉") 