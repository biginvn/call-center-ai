from app.websocket.ari.Config.ari_config import BASE_URL, AUTH, ARI_APP
import uuid
import requests
from app.websocket.ari.call_redis.call_redis import get_call, save_call, delete_call
from app.websocket.ari.Models.ari_models import CallSession

def hangup_channel(channel_id):
    """Hang up a channel"""
    try:
        r = requests.delete(
            f"{BASE_URL}/channels/{channel_id}",
            auth=AUTH
        )

        return r.status_code < 300
    except Exception as e:
        print(e)
        return False
    

def answer_channel(channel_id):
    print(f"Answering channel: {channel_id}")
    """Answer a channel"""
    r = requests.post(
        f"{BASE_URL}/channels/{channel_id}/answer",
        auth=AUTH
    )
    if r.status_code == 200:
        return True
    else:
        return False
    


def dial_to_agent(call_id, agent_extension, bridge_id, caller_name):
    """
    Dial to an agent and connect them to an existing call
    
    Args:
        agent_extension: The agent's extension to dial (e.g., 'test2')
        bridge_id: The bridge ID for this call
        caller_channel: The channel ID of the caller
        
    Returns:
        The agent's channel ID
    """
    # Create a unique channel ID for the agent
    agent_channel_id = f"agent_{agent_extension}_{uuid.uuid4().hex[:8]}"
    
    # Originate a call to the agent
    r = requests.post(
        f"{BASE_URL}/channels",
        auth=AUTH,
        params={
            "endpoint": f"PJSIP/{agent_extension}",
            "app": ARI_APP,
            "appArgs": f"agent,{bridge_id}",  # Mark as agent leg
            "channelId": agent_channel_id,
            "callerId": f"Customer Call <{caller_name}>"  # Show caller ID
        }
    )
    
    if r.status_code != 200:
        return None
        

    print(f"Dialing agent {agent_extension}...")
    
    # Store agent channel in call record
    call = get_call(call_id=call_id)
    if call:
        call.agent_chan = agent_channel_id
        call.agent_ext = agent_extension
        call.status = "ringing"
        save_call(call)

    
    return agent_channel_id
