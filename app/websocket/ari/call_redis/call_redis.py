from typing import List, Optional, Dict, Any
import redis
import json
from app.websocket.ari.Models.ari_models import CallSession
from app.core.config import settings
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)


def save_call(call: CallSession):
    # Convert CallSession to dict
    call_dict = call.dict()
    # Convert sets to lists for JSON serialization
    if "up" in call_dict:
        call_dict["up"] = list(call_dict["up"])
    if "bridged" in call_dict:
        call_dict["bridged"] = list(call_dict["bridged"])
    
    # Log call session data to file
    with open("log.txt", "a") as log_file:
        log_file.write(f"CALL SESSION: {json.dumps(call_dict, indent=2)}\n\n")
    
    r.set(f"call:{call.call_id}", json.dumps(call_dict))
    if call.caller_chan:
        r.set(f"channel:{call.caller_chan}", call.call_id)
    if call.agent_chan:
        r.set(f"channel:{call.agent_chan}", call.call_id)
        
def get_call_id_by_channel(channel_id: str) -> Optional[str]:
    return r.get(f"channel:{channel_id}")

def get_call(call_id: str) -> Optional[CallSession]:
    print("Getting call", call_id)
    key = f"call:{call_id}"
    raw = r.get(key)
    if raw:
        try:
            call_dict = json.loads(raw)
            # Convert lists back to sets
            if "up" in call_dict:
                call_dict["up"] = set(call_dict["up"])
            if "bridged" in call_dict:
                call_dict["bridged"] = set(call_dict["bridged"])
            print("Call found", call_dict)
            return CallSession(**call_dict)
        except Exception as e:
            print(f"Error parsing call data: {e}")
            return None
    return None
    
def delete_call(call_id: str):
    call = get_call(call_id)
    if not call:
        return
    r.delete(f"call:{call_id}")
    r.delete(f"channel:{call.caller_chan}")
    if call.agent_chan:
        r.delete(f"channel:{call.agent_chan}")

def list_calls() -> List[CallSession]:
    keys = r.keys("call:*")
    result = []
    for key in keys:
        raw = r.get(key)
        if raw:
            try:
                call_dict = json.loads(raw)
                # Convert lists back to sets
                if "up" in call_dict:
                    call_dict["up"] = set(call_dict["up"])
                if "bridged" in call_dict:
                    call_dict["bridged"] = set(call_dict["bridged"])
                result.append(CallSession(**call_dict))
            except Exception as e:
                print(f"Error parsing call data: {e}")
    return result


