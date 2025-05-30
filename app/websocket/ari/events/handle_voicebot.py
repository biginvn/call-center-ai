import aiohttp
from app.websocket.ari.Models.ari_models import CallSession
from app.websocket.ari.bridge.bridges import add_channels_to_bridge, create_mixing_bridge
from app.websocket.ari.call_redis.call_redis import save_call
from app.websocket.ari.channels.channels import answer_channel, dial_to_agent


# đầu tiên handle_voicebot nó sẽ originate call to voicebot
# sau đó sẽ handle_voicebot_answer nó sẽ answer call to voicebot
# sau đó sẽ handle_voicebot_bridge nó sẽ bridge call to voicebot

async def handle_voicebot(call: CallSession):
    print ("[handle_voicebot]")
    dial_to_agent(call.call_id, "voicebot", call.call_id, call.caller_ext)


async def handle_voicebot_answer(call: CallSession):
    print ("[handle_voicebot_answer]")
    answer_channel(call.agent_chan)
    call.status = "connected"
    save_call(call)