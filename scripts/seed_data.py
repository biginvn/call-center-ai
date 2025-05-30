import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from datetime import datetime
from typing import List, Dict
from app.core.config import settings
from app.repositories.base_repository import init_db, close_db, get_database
from app.models.user import User
from app.models.extension import Extension
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.enums import ConversationStatus, ConversationType, ConversationMood
from app.models.ai import AI
from beanie import Link
from bson import ObjectId
from pydantic import BaseModel


# Model tạm thời để lưu trữ message trong conversation trước khi lưu vào database
class TempMessage(BaseModel):
    id: str
    sender_id: str
    content: str
    mood: str
    order: int


async def reset_database():
    db = get_database()
    await db.drop_collection("User")
    await db.drop_collection("Extension")
    # await db.drop_collection("Conversation")
    # await db.drop_collection("Message")
    # await db.drop_collection("AI")

    print("Database đã được reset.")


async def seed_data():
    user_count = await User.count()
    if user_count > 0:
        print("Database đã có dữ liệu. Bỏ qua seeding.")
        return

    # Seed Users
    users = [
        User(
            username="admin",
            fullname="Admin",
            email="admin@gmail.com",
            password="123456",
            extension_number="",
            role="admin",
            status="",
        ),
        User(
            username="khoa",
            fullname="Lê Anh Khoa",
            email="khoa@gmail.com",
            password="123456",
            extension_number="",
            role="agent",
            status="",
        ),
        User(
            username="thanh",
            fullname="Nguyễn Phúc Thành",
            email="thanh@gmail.com",
            password="123456",
            extension_number="",
            role="agent",
            status="",
        ),
        User(
            username="manh",
            fullname="Trần Văn Mạnh",
            email="manh@gmail.com",
            password="123456",
            extension_number="",
            role="agent",
            status="",
        ),
        User(
            username="ai_bot",
            fullname="Trần Văn AI",
            email="ai@gmail.com",
            password="123456",
            extension_number="1000",
            role="agent",
            status="",
        ),
    ]

    # Insert Users and store in dictionary
    user_dict = {}
    for user in users:
        await user.insert()
        fetched_user = await User.get(user.id)  # Lấy lại user từ database
        user_dict[user.username] = fetched_user
        print(f"Đã thêm user: {user.username} với role: {user.role} và id: {user.id}")

    # Seed Extensions
    extensions = [
        Extension(extension="test1", number="100", available=True, user=None),
        Extension(extension="test2", number="101", available=True, user=None),
        Extension(extension="web1", number="111", available=True, user=None),
        Extension(extension="web2", number="112", available=True, user=None),
        Extension(extension="ai", number="1000", available=True, user=user_dict["ai_bot"]),
    ]

    # Insert Extensions
    for extension in extensions:
        await extension.insert()
        print(
            f"Đã thêm extension: {extension.extension} với number: {extension.number}"
        )

    ai_instructions = [
        AI(
            instructions=(
                "Bạn là một tổng đài viên ảo chuyên nghiệp, thân thiện và lịch sự, đại diện cho ngân hàng VPBank. Mục tiêu của bạn là lắng nghe, hiểu đúng nhu cầu của khách hàng và hỗ trợ hoặc điều hướng họ đến đúng bộ phận phù hợp.\n"
                "- Luôn chờ khách hàng nói xong rồi mới phản hồi.\n"
                "- Nếu khách hàng không phản hồi trong 5 giây, hãy nhắc lại nhẹ nhàng và kết thúc cuộc gọi sau 3 lần không phản hồi.\n"
                "- Nếu khách hàng thể hiện sự tức giận hoặc khó chịu, hãy nói lời xin lỗi nhẹ nhàng và xoa dịu tâm lý bằng giọng điệu đồng cảm.\n"
                "- Nếu khách hàng nói nhiều ý định trong một câu, hãy ưu tiên ý định đầu tiên để xử lý trước, sau đó hỏi thêm về ý định còn lại.\n"
                "- Không chen ngang khi khách hàng đang nói.\n"
                "- Có thể phản hồi tiếng Anh khi khách hàng dùng tiếng Anh. Nếu khách hàng dùng tiếng Việt pha tiếng Anh, hãy giữ nguyên ngôn ngữ phù hợp và phản hồi tự nhiên.\n"
                "- Khi khách hàng hỏi về các dòng thẻ, hãy cung cấp thông tin rõ ràng và chính xác, chỉ giới hạn trong các dòng thẻ sau:\n"
                "  - Thẻ ghi nợ: Diamond Debit\n"
                "  - Thẻ tín dụng: Lady, Shopee, Step Up, World, Number 1\n"
                "- Nếu không chắc chắn hoặc chưa hiểu rõ, hãy xin khách hàng nhắc lại hoặc hỏi rõ hơn.\n"
                "- Nếu khách hàng yêu cầu điều hướng đến bộ phận cụ thể (VD: tra cứu thẻ, khoản vay,...), hãy xác nhận lại và kết thúc cuộc gọi để chuyển hướng.\n"
                "- Nếu khách hàng hỏi câu hỏi không liên quan đến VPBank hoặc chủ đề về ngân hàng thì điều hướng đến tổng đài viên.\n"
                "Luôn đảm bảo tốc độ phản hồi nhanh (~2-3 giây), giọng nói rõ ràng, mạch lạc như người thật."
            ),
            voice="shimmer",
        )
    ]
    for instruction in ai_instructions:
        await instruction.insert()

    # Load conversations from data.json
    with open("scripts/data.json", "r", encoding="utf-8") as f:
        conversations_data = json.load(f)

    # # Process each conversation
    # for conv_data in conversations_data:
    #     # Create messages for this conversation
    #     messages = []
    #     for msg_data in conv_data['messages']:
    #         message = Message(
    #             sender_id=user_dict[msg_data['sender_id']],
    #             content=msg_data['content'],
    #             mood=msg_data['mood'],
    #             order=msg_data['order']
    #         )
    #         await message.insert()
    #         messages.append(message)
    #         print(f"Đã thêm message: {message.content} với mood: {message.mood}")

    #     # Create conversation
    #     conversation = Conversation(
    #         status=ConversationStatus.CLOSED,
    #         type=ConversationType.AGENT_TO_CUSTOMER,
    #         record_url=conv_data['record_url'],
    #         record_text=conv_data['record_text'],
    #         summarize=conv_data['summarize'],
    #         from_user=user_dict[conv_data['from_user']],
    #         to_user=user_dict[conv_data['to_user']],
    #         messages=messages,
    #         mood=ConversationMood.UNKNOWN,
    #         sentiment=conv_data['sentiment'],
    #         created_at=datetime.fromisoformat(conv_data['created_at'])
    #     )

    #     await conversation.insert()
    #     print(f"Đã thêm conversation từ {conv_data['from_user']} đến {conv_data['to_user']}")


async def main():
    await init_db()
    await reset_database()  # Reset database trước khi seed
    await seed_data()
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
