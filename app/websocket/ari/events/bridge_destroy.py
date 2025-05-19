from app.websocket.ari.call_redis.call_redis import delete_call


def handle_bridge_destroy(ev):
    bridge_id = ev["bridge"]["id"]
    
    delete_call(bridge_id)
    return