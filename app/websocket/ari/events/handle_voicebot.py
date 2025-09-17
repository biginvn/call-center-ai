import aiohttp
import asyncio
import logging
from app.websocket.ari.Models.ari_models import CallSession
from app.websocket.ari.bridge.bridges import add_channels_to_bridge, create_mixing_bridge
from app.websocket.ari.call_redis.call_redis import save_call
from app.websocket.ari.channels.channels import answer_channel, dial_to_agent
from app.services.voicebot_service import VoiceBotService

logger = logging.getLogger(__name__)

# Global voicebot service instance
voicebot_service = VoiceBotService()

async def handle_voicebot(call: CallSession):
    """
    Xử lý khi có cuộc gọi đến voicebot extension
    """
    try:
        logger.info(f"[handle_voicebot] Starting voicebot for call {call.call_id}")
        
        # Originate call tới voicebot extension (sử dụng extension 1000 thay vì voicebot)
        agent_chan = dial_to_agent(call.call_id, "1000", call.call_id, call.caller_ext)
        
        if not agent_chan:
            logger.error(f"Failed to originate call to voicebot for call {call.call_id}")
            return
        
        # Cập nhật call status
        call.agent_chan = agent_chan
        call.agent_ext = "voicebot"
        call.status = "ringing"
        save_call(call)
        
        logger.info(f"Voicebot call originated successfully for call {call.call_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_voicebot: {str(e)}")

async def handle_voicebot_answer(call: CallSession):
    """
    Xử lý khi voicebot channel được answer
    """
    try:
        logger.info(f"[handle_voicebot_answer] Answering voicebot for call {call.call_id}")
        
        # Answer voicebot channel
        answer_channel(call.agent_chan)
        
        # Cập nhật call status
        call.status = "connected"
        save_call(call)
        
        # Bắt đầu voicebot session
        await voicebot_service.start_voicebot_session(call)
        
        logger.info(f"Voicebot answered and session started for call {call.call_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_voicebot_answer: {str(e)}")

async def handle_voicebot_bridge(call: CallSession):
    """
    Xử lý khi bridge voicebot với caller
    """
    try:
        logger.info(f"[handle_voicebot_bridge] Bridging voicebot for call {call.call_id}")
        
        # Tạo bridge nếu chưa có
        if not call.bridge_id:
            bridge_id = create_mixing_bridge(conversation_id=call.call_id)
            call.bridge_id = bridge_id
            save_call(call)
        
        # Thêm cả hai channels vào bridge
        channels = [call.caller_chan, call.agent_chan]
        add_channels_to_bridge(call.bridge_id, channels)
        
        logger.info(f"Voicebot bridged successfully for call {call.call_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_voicebot_bridge: {str(e)}")

async def handle_voicebot_hangup(call: CallSession):
    """
    Xử lý khi voicebot call kết thúc
    """
    try:
        logger.info(f"[handle_voicebot_hangup] Ending voicebot session for call {call.call_id}")
        
        # Kết thúc voicebot session
        await voicebot_service.end_voicebot_session(call.call_id)
        
        # Cleanup channels và bridge
        await cleanup_voicebot_channels(call)
        
        logger.info(f"Voicebot session ended and channels cleaned up for call {call.call_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_voicebot_hangup: {str(e)}")

async def cleanup_voicebot_channels(call: CallSession):
    """
    Cleanup channels và bridge cho voicebot call
    """
    try:
        from app.websocket.ari.bridge.bridges import remove_channel_from_bridge, destroy_bridge
        from app.websocket.ari.channels.channels import hangup_channel
        
        # Remove channels từ bridge trước khi destroy
        if call.bridge_id:
            if call.caller_chan:
                try:
                    remove_channel_from_bridge(call.bridge_id, call.caller_chan)
                    logger.info(f"Removed caller channel {call.caller_chan} from bridge {call.bridge_id}")
                except Exception as e:
                    logger.warning(f"Error removing caller channel from bridge: {str(e)}")
            
            if call.agent_chan:
                try:
                    remove_channel_from_bridge(call.bridge_id, call.agent_chan)
                    logger.info(f"Removed agent channel {call.agent_chan} from bridge {call.bridge_id}")
                except Exception as e:
                    logger.warning(f"Error removing agent channel from bridge: {str(e)}")
            
            # Destroy bridge
            try:
                destroy_bridge(call.bridge_id)
                logger.info(f"Destroyed bridge {call.bridge_id}")
            except Exception as e:
                logger.warning(f"Error destroying bridge: {str(e)}")
        
        # Hangup channels nếu chưa bị hangup
        if call.caller_chan:
            try:
                hangup_channel(call.caller_chan)
                logger.info(f"Hung up caller channel {call.caller_chan}")
            except Exception as e:
                logger.warning(f"Error hanging up caller channel: {str(e)}")
        
        if call.agent_chan:
            try:
                hangup_channel(call.agent_chan)
                logger.info(f"Hung up agent channel {call.agent_chan}")
            except Exception as e:
                logger.warning(f"Error hanging up agent channel: {str(e)}")
        
        logger.info(f"Successfully cleaned up channels for call {call.call_id}")
        
    except Exception as e:
        logger.error(f"Error in cleanup_voicebot_channels: {str(e)}")