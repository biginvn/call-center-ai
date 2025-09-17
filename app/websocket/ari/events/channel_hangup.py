import asyncio
import logging
from app.websocket.ari.call_redis.call_redis import get_call_id_by_channel, get_call, delete_call
from app.websocket.ari.events.handle_voicebot import handle_voicebot_hangup, voicebot_service

logger = logging.getLogger(__name__)

def handle_channel_hangup(ev):
    """
    Xử lý khi channel bị hangup
    """
    try:
        channel_id = ev["channel"]["id"]
        logger.info(f"Channel hangup event: {channel_id}")
        
        # Tìm call liên quan đến channel này
        call_id = get_call_id_by_channel(channel_id)
        
        if not call_id:
            logger.warning(f"No call found for channel {channel_id}")
            return
        
        call = get_call(call_id)
        if not call:
            logger.warning(f"Call not found for id {call_id}")
            return
        
        # Kiểm tra xem có phải voicebot call không
        if voicebot_service.is_voicebot_extension(call.agent_ext):
            logger.info(f"Voicebot channel {channel_id} hung up for call {call_id}")
            
            # Xử lý voicebot hangup - chạy async
            try:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Chạy async function
                loop.run_until_complete(handle_voicebot_hangup(call))
            except Exception as e:
                logger.error(f"Error handling voicebot hangup: {str(e)}")
            
            # Xóa call khỏi Redis
            delete_call(call_id)
            logger.info(f"Deleted voicebot call {call_id} from Redis")
            
        else:
            # Regular call hangup
            logger.info(f"Regular call {call_id} hung up")
            delete_call(call_id)
            
    except Exception as e:
        logger.error(f"Error in handle_channel_hangup: {str(e)}")
