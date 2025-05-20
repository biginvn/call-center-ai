import requests
from app.websocket.ari.Config.ari_config import BASE_URL, AUTH, ARI_APP


def create_mixing_bridge(conversation_id):
    """Create a mixing bridge"""
    r = requests.post(
        f"{BASE_URL}/bridges",
        auth=AUTH,
            params={"type": "mixing", "app": ARI_APP, "bridgeId": conversation_id}
    )

    r.raise_for_status()
    return r.json()["id"]



def add_channels_to_bridge(bridge_id, channels):
    print(f"Adding channels to bridge: {bridge_id} - {channels}")
    """Add channels to a bridge"""
    r = requests.post(
        f"{BASE_URL}/bridges/{bridge_id}/addChannel",
        auth=AUTH,
        json={"channel": channels}
    )
    r.raise_for_status()
def destroy_bridge(conversation_id):
    """Destroy a bridge"""
    try:
        r = requests.delete(
            f"{BASE_URL}/bridges/{conversation_id}",
            auth=AUTH
        )
        return r.status_code < 300
    except Exception as e:
        print(e)
        return False