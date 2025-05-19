from app.websocket.ari.call_utils.ari_call_utils import connect_call
from app.websocket.ari.channels.channels import answer_channel
from app.websocket.ari.call_redis.call_redis import list_calls, save_call

def handle_channel_state_change(ev):
    chan = ev["channel"]["id"]
    if not ev["channel"]["state"] == "Up":
        return
    # Find which call this channel belongs to
    for call in list_calls():
        # Check if this is either a caller or agent channel
        print(f"CHANNEL_UP: chan={chan} call={call.call_id}")
        if chan in (call.caller_chan, call.agent_chan):
            # Add to up set
            call.up.add(chan)
            
            # If this is the agent channel going Up, connect the call
            if chan == call.agent_chan:
                print(f"ANSWERING CALLER CHANNEL: {call.caller_chan}")
                # Answer caller's channel now that agent has answered
                if call.caller_chan:
                    answer_channel(call.caller_chan)

            save_call(call)
            # Now that agent has answered, connect both channels to bridge
            connect_call(call.call_id)
        
            break