from app.websocket.ari.call_utils.ari_call_utils import connect_call
from app.websocket.ari.channels.channels import answer_channel
from app.websocket.ari.call_redis.call_redis import list_calls, save_call
from app.websocket.ari.events.handle_voicebot import handle_voicebot_answer, handle_voicebot_bridge, voicebot_service
import asyncio
import logging

logger = logging.getLogger(__name__)

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

                # Kiểm tra xem có phải voicebot không
                if voicebot_service.is_voicebot_extension(call.agent_ext):
                    logger.info(f"Voicebot channel {chan} is up for call {call.call_id}")
                    # Xử lý voicebot answer
                    asyncio.create_task(handle_voicebot_answer(call))
                    # Bridge voicebot với caller
                    asyncio.create_task(handle_voicebot_bridge(call))
                else:
                    # Regular agent connection
                    connect_call(call.call_id)

            save_call(call)
        
            break