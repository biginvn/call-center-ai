from app.websocket.ari.call_redis.call_redis import get_call_id_by_channel, get_call
from app.websocket.ari.call_utils.ari_call_utils import end_call

def handle_hangup_request(ev):
    chan = ev["channel"]["id"]
    call_id = get_call_id_by_channel(chan)

    if not call_id:
        print(f"[WARN] No call associated with channel {chan}")
        return

    call = get_call(call_id)
    if not call:
        print(f"[WARN] Call not found for id {call_id}")
        return

    end_call(call.call_id)
