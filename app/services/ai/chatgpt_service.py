import openai
import logging
from typing import List, Dict, Optional
from app.core.config import settings
from app.models.voicebot import ChatGPTRequest, ChatGPTResponse

logger = logging.getLogger(__name__)

class ChatGPTService:
    """Service xử lý hội thoại AI sử dụng OpenAI ChatGPT API"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.system_prompt = """Bạn là một trợ lý AI thông minh và hữu ích. 
        
Hướng dẫn quan trọng:
- Giữ câu trả lời ngắn gọn và súc tích (tối đa 2-3 câu) vì đây là cuộc gọi điện thoại
- Nói chuyện một cách tự nhiên và thân thiện
- Trả lời bằng tiếng Việt trừ khi được yêu cầu khác
- Nếu không hiểu câu hỏi, hãy yêu cầu người dùng nói rõ hơn
- Luôn lịch sự và chuyên nghiệp
- Tránh đưa ra lời khuyên y tế, pháp lý hoặc tài chính quan trọng
- Nếu cần thông tin chi tiết, hãy đề xuất người dùng liên hệ với chuyên gia"""
    
    async def get_response(self, request: ChatGPTRequest) -> ChatGPTResponse:
        """
        Lấy phản hồi từ ChatGPT
        
        Args:
            request: ChatGPTRequest chứa tin nhắn và cấu hình
            
        Returns:
            ChatGPTResponse với phản hồi từ AI
        """
        try:
            logger.info(f"Gửi tin nhắn tới ChatGPT: {len(request.message)} ký tự")
            
            # Xây dựng danh sách messages
            messages = []
            
            # Thêm system prompt
            system_prompt = request.system_prompt or self.system_prompt
            messages.append({"role": "system", "content": system_prompt})
            
            # Thêm lịch sử hội thoại
            if request.conversation_history:
                # Giới hạn lịch sử để tránh vượt quá token limit
                recent_history = request.conversation_history[-10:]  # Chỉ lấy 10 tin nhắn gần nhất
                messages.extend(recent_history)
            
            # Thêm tin nhắn hiện tại
            messages.append({"role": "user", "content": request.message})
            
            # Gọi ChatGPT API
            response = await self.client.chat.completions.create(
                model=request.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content
            usage_info = response.usage.dict() if response.usage else None
            
            logger.info(f"Nhận phản hồi từ ChatGPT: {len(ai_response)} ký tự")
            
            return ChatGPTResponse(
                response=ai_response,
                usage=usage_info,
                model=response.model
            )
            
        except Exception as e:
            logger.error(f"Lỗi khi gọi ChatGPT API: {str(e)}")
            # Trả về phản hồi mặc định khi có lỗi
            return ChatGPTResponse(
                response="Xin lỗi, tôi gặp một chút khó khăn. Bạn có thể nói lại được không?",
                usage=None,
                model=self.model
            )
    
    async def get_response_simple(self, message: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Phương thức đơn giản để lấy phản hồi từ ChatGPT
        
        Args:
            message: Tin nhắn từ người dùng
            conversation_history: Lịch sử hội thoại
            
        Returns:
            Phản hồi từ AI
        """
        try:
            request = ChatGPTRequest(
                message=message,
                conversation_history=conversation_history or [],
                max_tokens=150,
                temperature=0.7
            )
            
            response = await self.get_response(request)
            return response.response
            
        except Exception as e:
            logger.error(f"Lỗi ChatGPT đơn giản: {str(e)}")
            return "Xin lỗi, tôi gặp một chút khó khăn. Bạn có thể nói lại được không?"
    
    async def create_contextual_response(self, user_input: str, context: Dict[str, str]) -> str:
        """
        Tạo phản hồi có ngữ cảnh
        
        Args:
            user_input: Đầu vào từ người dùng
            context: Thông tin ngữ cảnh (tên, thời gian, v.v.)
            
        Returns:
            Phản hồi có ngữ cảnh
        """
        try:
            # Tạo system prompt có ngữ cảnh
            contextual_prompt = self.system_prompt
            
            if context.get("caller_name"):
                contextual_prompt += f"\nNgười gọi tên là: {context['caller_name']}"
            
            if context.get("time_of_day"):
                contextual_prompt += f"\nThời gian hiện tại: {context['time_of_day']}"
            
            if context.get("call_purpose"):
                contextual_prompt += f"\nMục đích cuộc gọi: {context['call_purpose']}"
            
            request = ChatGPTRequest(
                message=user_input,
                system_prompt=contextual_prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            response = await self.get_response(request)
            return response.response
            
        except Exception as e:
            logger.error(f"Lỗi tạo phản hồi có ngữ cảnh: {str(e)}")
            return "Xin lỗi, tôi gặp một chút khó khăn. Bạn có thể nói lại được không?"
    
    async def handle_greeting(self, user_input: str) -> str:
        """
        Xử lý lời chào từ người dùng
        
        Args:
            user_input: Lời chào từ người dùng
            
        Returns:
            Phản hồi chào hỏi phù hợp
        """
        greeting_prompt = """Bạn là một trợ lý AI thân thiện. 
Người dùng vừa chào bạn. Hãy chào lại một cách tự nhiên và hỏi xem bạn có thể giúp gì cho họ.
Giữ câu trả lời ngắn gọn (1-2 câu)."""
        
        request = ChatGPTRequest(
            message=user_input,
            system_prompt=greeting_prompt,
            max_tokens=100,
            temperature=0.8
        )
        
        response = await self.get_response(request)
        return response.response
    
    async def handle_goodbye(self, user_input: str) -> str:
        """
        Xử lý lời tạm biệt từ người dùng
        
        Args:
            user_input: Lời tạm biệt từ người dùng
            
        Returns:
            Phản hồi tạm biệt phù hợp
        """
        goodbye_prompt = """Bạn là một trợ lý AI lịch sự.
Người dùng vừa nói lời tạm biệt. Hãy chúc họ một ngày tốt lành và kết thúc cuộc trò chuyện một cách lịch sự.
Giữ câu trả lời ngắn gọn (1 câu)."""
        
        request = ChatGPTRequest(
            message=user_input,
            system_prompt=goodbye_prompt,
            max_tokens=50,
            temperature=0.7
        )
        
        response = await self.get_response(request)
        return response.response
    
    async def handle_question(self, user_input: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Xử lý câu hỏi từ người dùng
        
        Args:
            user_input: Câu hỏi từ người dùng
            conversation_history: Lịch sử hội thoại
            
        Returns:
            Phản hồi cho câu hỏi
        """
        return await self.get_response_simple(user_input, conversation_history)
    
    def is_greeting(self, text: str) -> bool:
        """
        Kiểm tra xem văn bản có phải là lời chào không
        
        Args:
            text: Văn bản cần kiểm tra
            
        Returns:
            True nếu là lời chào, False nếu không
        """
        greetings = [
            "xin chào", "chào", "hello", "hi", "hey", "chào bạn", "chào anh", "chào chị",
            "chào em", "good morning", "good afternoon", "good evening", "chào buổi sáng",
            "chào buổi chiều", "chào buổi tối"
        ]
        
        text_lower = text.lower().strip()
        return any(greeting in text_lower for greeting in greetings)
    
    def is_goodbye(self, text: str) -> bool:
        """
        Kiểm tra xem văn bản có phải là lời tạm biệt không
        
        Args:
            text: Văn bản cần kiểm tra
            
        Returns:
            True nếu là lời tạm biệt, False nếu không
        """
        goodbyes = [
            "tạm biệt", "bye", "goodbye", "chào tạm biệt", "hẹn gặp lại", "cảm ơn",
            "thank you", "cảm ơn bạn", "kết thúc", "dừng lại", "thôi", "được rồi"
        ]
        
        text_lower = text.lower().strip()
        return any(goodbye in text_lower for goodbye in goodbyes)
    
    def clean_response(self, response: str) -> str:
        """
        Làm sạch phản hồi từ AI
        
        Args:
            response: Phản hồi thô từ AI
            
        Returns:
            Phản hồi đã được làm sạch
        """
        # Loại bỏ các ký tự không cần thiết
        cleaned = response.strip()
        
        # Loại bỏ các từ không phù hợp cho cuộc gọi
        inappropriate_phrases = [
            "tôi không thể", "tôi không biết", "tôi không hiểu"
        ]
        
        for phrase in inappropriate_phrases:
            if phrase in cleaned.lower():
                cleaned = "Tôi sẽ cố gắng giúp bạn. Bạn có thể nói rõ hơn được không?"
                break
        
        return cleaned
