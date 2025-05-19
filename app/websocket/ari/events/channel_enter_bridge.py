from app.websocket.ari.call_redis.call_redis import get_call, list_calls




def handle_channel_enter_bridge(ev):
    bridge_id = ev["bridge"]["id"]
    chan = ev["channel"]["id"]
    
    # Look for the call record with this bridge
    for call_id in list_calls():
        call = get_call(call_id)
        if call.bridge_id == bridge_id:
            # Track that this channel is in the bridge
            call.bridged.add(chan)
            
            # If both channels are bridged, call is established
            if len(call.bridged) == 2:
                # Mark call as connected - important for WebRTC UI
                call.status = "connected"
                print(f"Call established: bridge={bridge_id}")
            
            break