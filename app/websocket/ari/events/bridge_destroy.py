from http.client import HTTPException
from app.models.conversation import Conversation
from app.models.enums import ConversationMood, ConversationStatus, ConversationType
from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.websocket.ari.Config.ari_config import ARI_HOST, ARI_HTTPS_PORT, BASE_URL
from app.websocket.ari.call_redis.call_redis import delete_call, get_call
from app.services.ai_service import AIService, gpt_call_analyze_response
from app.websocket.ari.events.handle_voicebot import handle_voicebot_hangup, voicebot_service
import asyncio
import logging

logger = logging.getLogger(__name__)


async def handle_bridge_destroy(ev):
    try:
        print("Bridge destroy event", ev)
        bridge_id = ev["bridge"]["id"]
        call = get_call(bridge_id)
        print ("Phone call from: ", call.caller_ext, " to: ", call.agent_ext)
        
        # Kiểm tra xem có phải voicebot call không
        if voicebot_service.is_voicebot_extension(call.agent_ext):
            logger.info(f"Voicebot call ended for call {bridge_id}")
            # Xử lý voicebot hangup
            await handle_voicebot_hangup(call)
            # Không cần xử lý conversation cho voicebot
            delete_call(bridge_id)
            return
        print("Mapping channel to user")
        from_user = await UserRepository.get_user_by_extension(call.caller_ext)
        to_user = await UserRepository.get_user_by_extension(call.agent_ext)
        # if not from_user or not from_user.id:
        #     raise HTTPException(status_code=404, detail="from_user không tồn tại hoặc chưa có id")

        # if not to_user or not to_user.id:
        #     raise HTTPException(status_code=404, detail="to_user không tồn tại hoặc chưa có id")
        print("From user ID:", from_user.id)
        print("To user ID:", to_user.id)
        record_url = f"https://{ARI_HOST}:{ARI_HTTPS_PORT}/ari/recordings/stored/{call.recording_name}/file"
        
        ai_service = AIService()
        file_url = await ai_service.upload_record_to_s3(record_url, from_user.username)
        # file_url = "https://internship-nixxis.s3.ap-southeast-1.amazonaws.com/records/54259aab-c02c-47b7-bd5b-281999e44c54.wav"
        print("File uploaded to S3:", file_url)
        ai_response: gpt_call_analyze_response = await ai_service.analyze_call_full_one_gpt_call(file_url, call.caller_ext, call.agent_ext)
        print("AI response:", ai_response)
        call_messages = []
        for mes in ai_response.messages:
            message = Message(
                sender_id=mes.sender_id,
                content=mes.content,
                mood=mes.mood,
                order=mes.order,
                start_time=mes.start_time,
                end_time=mes.end_time
        )
            await message.insert()
            call_messages.append(message)
            
        # save_messages = await MessageRepository.create_messages(messages)
        try:
            conversation = Conversation(
                type=ConversationType.AGENT_TO_CUSTOMER,
                from_user=from_user,
                to_user=to_user,
                status=ConversationStatus.CLOSED,
                record_url=file_url,
                mood=ConversationMood.UNKNOWN,
                messages=call_messages,
                summarize=ai_response.summarize,
                sentiment=ai_response.overall_mood,
                client_id=from_user.client_id
            )
            print("Conversation object created successfully")
            
            try:
                print("Attempting to save conversation...")
                saved_conversation = await ConversationRepository.create_conversation(conversation)
                print("Conversation saved successfully:", saved_conversation)
            except Exception as save_error:
                print("Error saving conversation:", str(save_error))
                raise save_error
                
        except Exception as create_error:
            print("Error creating conversation object:", str(create_error))
            raise create_error
            
        delete_call(bridge_id)
        print("Call deleted")
        return
        
    except Exception as e:
        print("Error in handle_bridge_destroy:", str(e))
        raise e 