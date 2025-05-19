from app.websocket.ari.channels.channels import hangup_channel
from app.websocket.ari.bridge.bridges import add_channels_to_bridge, create_mixing_bridge, destroy_bridge
from app.websocket.ari.recordings.recordings import start_recording, stop_recording
from app.websocket.ari.call_redis.call_redis import delete_call, get_call, save_call










def end_call(call_id):

    call = get_call(call_id)
    if not call:
        return False

    # Stop recording if active
    stop_recording(call_id)

    # Hang up any snoop channels
    if "snoops" in call:
        for snoop_id in call["snoops"]:
            hangup_channel(snoop_id)


    # Hang up agent and caller channels
    if call.agent_chan:
        hangup_channel(call.agent_chan)
    
    if call.caller_chan:
        hangup_channel(call.caller_chan)

    # Destroy the bridge if it exists
    if call.bridge_id:
        destroy_bridge(call.bridge_id)
    
    # Remove call from active calls
    # delete_call(call_id)

    print(f"Call ended: {call_id}")
    
    return True

def connect_call(call_id):
    """Create a bridge and connect both channels once agent has answered"""
    call = get_call(call_id)
    if not call:
        print(f"CONNECT_FAILED: Call not found: {call_id}")
        return False
        
    # Make sure we have both channels
    if not call.caller_chan or not call.agent_chan:
        print(f"CONNECT_FAILED: Missing channels for call {call_id}")
        return False
    
    # Check if agent channel is ready (must be up)
    if call.agent_chan not in call.up:
        print(f"CONNECT_FAILED: Agent not ready for call {call_id}")
        return False
    
    # Create bridge if not exists
    if not call.bridge_id:
        try:
            bridge_id = create_mixing_bridge(conversation_id=call.call_id)
            call.bridge_id = bridge_id
            print(f"BRIDGE_CREATED: bridge={bridge_id} for call={call_id}")
        except Exception as e:
            print(f"BRIDGE_CREATION_ERROR: {e} for call={call_id}")
            return False
    
    # Add both channels to bridge ONLY when agent has answered
    if call.agent_chan in call.up:
        channels = [call.caller_chan, call.agent_chan]
        try:
            add_channels_to_bridge(call.bridge_id, channels)
            print(f"CHANNELS_ADDED_TO_BRIDGE: channels={channels} bridge={call.bridge_id}")
            print(f"Call connected: {call_id}")
            
            # Set call status as connected
            call.status = "connected"
            # Start recording the call
            start_recording(call_id)
            save_call(call)
            return True
        except Exception as e:
            print(f"ADD_CHANNELS_ERROR: {e} for call={call_id}")
            return False
    
    return False