from app.websocket.ari.Models.ari_models import StasisStartEvent
import uuid
import asyncio
import logging
from app.websocket.ari.Models.ari_models import CallSession
from app.websocket.ari.channels.channels import dial_to_agent
from app.websocket.ari.call_redis.call_redis import get_call, get_call_id_by_channel, save_call
from app.websocket.ari.events.handle_voicebot import handle_voicebot, voicebot_service

logger = logging.getLogger(__name__)
def handle_stasis_start(ev):
    stasis_start = StasisStartEvent(**ev)
    chan = stasis_start.channel.id
    bridge_id = str(uuid.uuid4())
    calle_endpoints_name = stasis_start.args[0]
    caller_name = stasis_start.channel.caller.name or "N/A"
    if not calle_endpoints_name:
        return
    existing_call = get_call( get_call_id_by_channel(chan))

    if existing_call and existing_call.status == "ringing":
        return
    # Case 3: Incoming call from dialplan


    caller_num = stasis_start.channel.caller.number
    
    # Create call record with caller channel
    call: CallSession = CallSession(
        call_id = bridge_id,
        caller_chan = chan,
        agent_chan = None,
        bridge_id = None,
        bridged = set(),
        up = set(),
        status = "incoming",  # Set initial status
        conversation_id = None,
        snoops = None,
        recording_name = bridge_id,
        recording_finished = None,
        agent_ext = None,
        caller_ext = ev["channel"]["caller"]["number"]
    )

    save_call(call)
    
    # DO NOT ANSWER the caller's channel - let it ring until agent answers
    # answer_channel(chan) - REMOVED THIS LINE, caller should stay ringing
    
    print(f"Incoming call from {caller_num}, bridge={bridge_id}")
    print(f"calle_endpoints_name={calle_endpoints_name}")
    
    # Kiểm tra xem có phải voicebot extension không
    if voicebot_service.is_voicebot_extension(calle_endpoints_name):
        logger.info(f"Voicebot call detected for extension: {calle_endpoints_name}")
        # Xử lý voicebot call
        asyncio.create_task(handle_voicebot(call))
    else:
        # Dial to regular agent
        logger.info(f"Regular agent call for extension: {calle_endpoints_name}")
        agent_chan = dial_to_agent(bridge_id, calle_endpoints_name, bridge_id, caller_name)