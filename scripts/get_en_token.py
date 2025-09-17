import requests
import os

def get_en_token():
    """Login and get ephemeral session token (enToken) for OpenAI Realtime API."""
    # Replace with your backend URL
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    session = requests.Session()
    
    # 1. Login
    login_resp = session.post(f"{backend_url}/login/agent", json={
        "username": "nixxisdevteam",
        "password": "nixxisdevteam",
        "extension_number": "116"
    })
    login_resp.raise_for_status()
    login_data = login_resp.json()
    access_token = login_data.get("access_token")
    print("Login successful.")

    if not access_token:
        print("❌ Không nhận được access_token từ login response")
        return None

    # 2. Get /realtime/session
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    session_resp = session.get(f"{backend_url}/realtime/session", headers=headers)
    session_resp.raise_for_status()
    data = session_resp.json()
    en_token = data["client_secret"]["value"]
    print(f"enToken: {en_token}")
    return en_token

if __name__ == "__main__":
    get_en_token()
