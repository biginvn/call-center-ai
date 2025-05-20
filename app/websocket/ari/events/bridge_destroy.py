from app.models.conversation import Conversation
from app.models.enums import ConversationMood, ConversationStatus, ConversationType
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.websocket.ari.Config.ari_config import ARI_HOST, ARI_HTTPS_PORT, BASE_URL
from app.websocket.ari.call_redis.call_redis import delete_call, get_call
from app.services.ai_service import AIService


async def handle_bridge_destroy(ev):
    try:
        print("Bridge destroy event", ev)
        bridge_id = ev["bridge"]["id"]
        call = get_call(bridge_id)
        print ("Phone call from: ", call.caller_ext, " to: ", call.agent_ext)
        print("Mapping channel to user")
        from_user = await UserRepository.get_user_by_extension(call.caller_ext)
        to_user = await UserRepository.get_user_by_extension(call.agent_ext)
        print("From user ID:", from_user.id)
        print("To user ID:", to_user.id)

        print("Creating conversation")
        print ("CallId:", call.call_id)
        print ("From user:", from_user)
        print ("To user:", to_user)
        print ("Conversation type:", ConversationType.AGENT_TO_AGENT)
        print ("Conversation status:", ConversationStatus.CLOSED)
        print ("Conversation record_url:", call.recording_name)
        print ("Conversation mood:", ConversationMood.UNKNOWN)
        record_url = f"https://{ARI_HOST}:{ARI_HTTPS_PORT}/ari/recordings/stored/{call.recording_name}/file"
        
        ai_service = AIService()
        document = await ai_service.upload_record_to_s3(record_url, from_user.username)
        record_text = await ai_service.transcribe_wav_from_s3(document.file_path)
        summarize = await ai_service.summarize_text(record_text)
        try:
            conversation = Conversation(
                type=ConversationType.AGENT_TO_CUSTOMER,
                from_user=from_user,
                to_user=to_user,
                record_text=record_text,
                status=ConversationStatus.CLOSED,
                record_url=record_url,
                mood=ConversationMood.UNKNOWN,
                messages=[],
                summarize=summarize,
                sentiment=""
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