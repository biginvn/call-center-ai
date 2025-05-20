from app.websocket.ari.Config.ari_config import BASE_URL, AUTH
import requests
from app.websocket.ari.Models.ari_models import CallSession
from app.websocket.ari.call_redis.call_redis import get_call, save_call






def start_recording(call_id):
    """Start recording a call using ARI recording API"""
    call = get_call(call_id)
    if not call or not call.bridge_id:
        print(f"RECORDING_FAILED: No active bridge for call {call_id}")
        return False
    
    # Start recording the bridge
    try:
        r = requests.post(
            f"{BASE_URL}/bridges/{call.bridge_id}/record",
            auth=AUTH,
            params={
                "name": call_id,
                "format": "wav",
                "maxDurationSeconds": 3600,  # 1 hour max
                "beep": False,  # Don't play beep when recording starts
                "terminateOn": "none"  # Don't stop recording automatically
            }
        )

        if r.status_code == 200:
            resp = r.json()
            state = resp.get("state", "")
            call.recording_name = call_id
            save_call(call)
            if state != "recording":
                print(f"RECORDING_QUEUED: call={call_id} state={state}")
            else:
                print(f"RECORDING_STARTED: call={call_id}")
            return True

    except Exception as e:
        print(e)
        return False
def stop_recording(call_id):
    """Stop recording a call"""
    call = get_call(call_id)
    if not call or not call.recording_name:
        return False
    
    try:
        r = requests.post(
            f"{BASE_URL}/recordings/{call.recording_name}/stop",
            auth=AUTH
        )
        
        if r.status_code < 300:
            # print(f"RECORDING_STOPPED: call={call_id} file={call.get('recording_file', 'unknown')}")
            return True
        else:
            print(f"RECORDING_STOP_FAILED: call={call_id} error={r.text}")
            return False
    except Exception as e:
        print(e)
        return False
