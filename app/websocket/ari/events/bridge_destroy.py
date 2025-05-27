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


async def handle_bridge_destroy(ev):
    try:
        print("Bridge destroy event", ev)
        bridge_id = ev["bridge"]["id"]
        call = get_call(bridge_id)
        print ("Phone call from: ", call.caller_ext, " to: ", call.agent_ext)
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
        print("File uploaded to S3:", file_url)
        ai_response: gpt_call_analyze_response = await ai_service.analyze_call_full_one_gpt_call(file_url, call.caller_ext, call.agent_ext)
        print("AI response:", ai_response)
        call_messages = []
        for mes in ai_response.messages:
            message = Message(
                sender_id=from_user.id if mes.sender_id == "from_user" else to_user.id,
                content=mes.content,
                mood=mes.mood,
                order=mes.order,
                time=mes.time
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
                sentiment=ai_response.overall_mood
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