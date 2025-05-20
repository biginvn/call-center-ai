from app.websocket.ari.call_redis.call_redis import get_call, list_calls


def handle_recording_finished(ev):
    name = ev["recording"].get("name")

    # Find the call using recording name
    for call in list_calls():
        
        if call.recording_name == name:
            call.recording_finished = True
            print(f"Recording finished: call={call.call_id} file={name}")
            break