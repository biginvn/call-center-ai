import sys
import os
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
    await db.drop_collection("Conversation")
    await db.drop_collection("Message")
    print("Database đã được reset.")
   

async def seed_data():
    user_count = await User.count()
    if user_count > 0:
        print("Database đã có dữ liệu. Bỏ qua seeding.")
        return

    # Seed Users
    users = [
        User(
            id=ObjectId("682d9de38a34a22cf819acea"),
            username="test1",
            fullname="Nguyễn Phúc A",
            email="test1@gmail.com",
            password="123456",
            extension_number="test1",
            role="agent",
            status=""
        ),
        User(
            id=ObjectId("682d9de38a34a22cf819aceb"),
            username="test2",
            fullname="Nguyễn Phúc B",
            email="test2@gmail.com",
            password="123456",
            extension_number="test2",
            role="agent",
            status=""
        ),
        User(
            username="admin",
            fullname="Admin",
            email="admin@gmail.com",
            password="123456",
            extension_number="",
            role="admin",
            status=""
        ),
        User(
            username="khoa",
            fullname="Lê Anh Khoa",
            email="khoa@gmail.com",
            password="123456",
            extension_number="",
            role="agent",
            status=""
        ),
        User(
            username="thanh",
            fullname="Nguyễn Phúc Thành",
            email="thanh@gmail.com",
            password="123456",
            extension_number="",
            role="agent",
            status=""
        ),
        User(
            username="manh",
            fullname="Trần Văn Mạnh",
            email="manh@gmail.com",
            password="123456",
            extension_number="",
            role="agent",
            status=""
        ),
    ]

    # Insert Users and store in dictionary
    user_dict = {}
    for user in users:
        await user.insert()
        fetched_user = await User.get(user.id)  # Lấy lại user từ database
        user_dict[str(user.id)] = fetched_user
        print(f"Đã thêm user: {user.username} với role: {user.role} và id: {user.id}")

    # Seed Extensions
    extensions = [
        Extension(extension="test1", number="100", available=True),
        Extension(extension="test2", number="101", available=True),
        Extension(extension="web1", number="111", available=True),
        Extension(extension="web2", number="112", available=True),
    ]

    # Insert Extensions
    for extension in extensions:
        await extension.insert()
        print(f"Đã thêm extension: {extension.extension} với number: {extension.number}")

    messages = [
        Message(
            sender_id=user_dict["682d9de38a34a22cf819aceb"],
            content="Alo cửa hàng ABC xin nghe ạ",
            mood="neutral",
            order=1
        ),
        Message(
            sender_id=user_dict["682d9de38a34a22cf819acea"],
            content="Chào shop, cho mình hỏi là bên mình còn áo sơ mi trắng không ạ?",
            mood="neutral",
            order=2
        ),
        Message(
            sender_id=user_dict["682d9de38a34a22cf819aceb"],
            content="Dạ, anh muốn giữ hàng không ạ?",
            mood="neutral",
            order=3
        ),
        Message(
            sender_id=user_dict["682d9de38a34a22cf819acea"],
            content="Cho anh giữ cho mình giúp một cái nha, chiều mình sẽ qua lấy.",
            mood="neutral",
            order=4
        ),
        Message(
            sender_id=user_dict["682d9de38a34a22cf819aceb"],
            content="Dạ vâng, em giữ hàng cho anh nha, cảm ơn anh đã gọi.",
            mood="positive",
            order=5
        ),
        Message(
            sender_id=user_dict["682d9de38a34a22cf819acea"],
            content="Dạ, cảm ơn.",
            mood="positive",
            order=6
        ),
    ]
    saved_messages = []
    for messsage in messages:
        saved_message = TempMessage(
            id=str(ObjectId()),
            sender_id=message.sender_id,
            content=message.content,
            mood=message.mood,
            order=message.order
        )
        saved_messages.append(saved_message)
    saved_messages.insertMany()

    # Insert Messages
    message_dict = {}
    for message in messages:
        await message.insert()
        fetched_message = await Message.get(message.id)  # Lấy lại message từ database
        message_dict[str(message.id)] = fetched_message
        print(f"Đã thêm message: {message.content} với mood: {message.mood}")

    # Seed Conversations
    conversations = [
        Conversation(
            id=ObjectId("682da273ebc9b1b7b0c3777c"),
            status=ConversationStatus.CLOSED,
            type=ConversationType.AGENT_TO_CUSTOMER,
            record_url="https://internship-nixxis.s3.ap-southeast-1.amazonaws.com/records/d938498f-73b3-4be9-82aa-0f959be1ebb2.wav",
            record_text="A lô, cửa hàng ABC xin nghe. Chào sếp, thì cho mình hỏi là bên mình có 1 cái áo xanh trắng xa lờ không? Dạ, anh muốn giữ hàng không ạ? Có, anh giữ cho mình giúp 1 cái nha. Chiều mình sẽ qua lát. Dạ vâng, em giữ hàng cho anh nha. Cảm ơn anh đã gọi. Dạ, cảm ơn.\n",
            summarize="Khách hàng gọi đến cửa hàng ABC để hỏi về một áo xanh trắng. Nhân viên xác nhận có hàng và hỏi khách có muốn giữ không. Khách yêu cầu giữ một chiếc và cho biết sẽ đến lấy vào chiều. Nhân viên đồng ý giữ hàng và cảm ơn khách.",
            from_user=user_dict["682d9de38a34a22cf819acea"],
            to_user=user_dict["682d9de38a34a22cf819aceb"],
            messages=[
                message for message in saved_messages
            ],
            mood=ConversationMood.UNKNOWN,
            sentiment="",
            created_at=datetime.fromisoformat("2025-05-21T09:52:51.156000")
        ),
    ]
    
    for conversation in conversations:
        await conversation.insert()
        print(f"Đã thêm conversation: {conversation.type} với status: {conversation.status}")
async def main():
    await init_db()
    await reset_database()  # Reset database trước khi seed
    await seed_data()
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())