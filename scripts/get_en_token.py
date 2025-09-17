import requests
import os

def get_en_token():
    """Login and get ephemeral session token (enToken) for OpenAI Realtime API."""
    # Replace with your backend URL
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    session = requests.Session()
    
    # 1. Login
    login_resp = session.post(f"{backend_url}/login", json={
        "username": "volkan1",
        "password": "volkan123"
    })
    login_resp.raise_for_status()
    print("Login successful.")

    # 2. Get /realtime/session
    session_resp = session.get(f"{backend_url}/realtime/session")
    session_resp.raise_for_status()
    data = session_resp.json()
    en_token = data["client_secret"]["value"]
    print(f"enToken: {en_token}")
    return en_token

if __name__ == "__main__":
    get_en_token()
