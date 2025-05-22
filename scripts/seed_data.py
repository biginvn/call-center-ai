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
        user_dict[user.username] = fetched_user
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
 
    # Load conversations from data.json
    with open('scripts/data.json', 'r', encoding='utf-8') as f:
        conversations_data = json.load(f)
 
    # Process each conversation
    for conv_data in conversations_data:
        # Create messages for this conversation
        messages = []
        for msg_data in conv_data['messages']:
            message = Message(
                sender_id=user_dict[msg_data['sender_id']],
                content=msg_data['content'],
                mood=msg_data['mood'],
                order=msg_data['order']
            )
            await message.insert()
            messages.append(message)
            print(f"Đã thêm message: {message.content} với mood: {message.mood}")
 
        # Create conversation
        conversation = Conversation(
            status=ConversationStatus.CLOSED,
            type=ConversationType.AGENT_TO_CUSTOMER,
            record_url=conv_data['record_url'],
            record_text=conv_data['record_text'],
            summarize=conv_data['summarize'],
            from_user=user_dict[conv_data['from_user']],
            to_user=user_dict[conv_data['to_user']],
            messages=messages,
            mood=ConversationMood.UNKNOWN,
            sentiment=conv_data['sentiment'],
            created_at=datetime.fromisoformat(conv_data['created_at'])
        )
        
        await conversation.insert()
        print(f"Đã thêm conversation từ {conv_data['from_user']} đến {conv_data['to_user']}")
 
async def main():
    await init_db()
    await reset_database()  # Reset database trước khi seed
    await seed_data()
    await close_db()
 
if __name__ == "__main__":
    asyncio.run(main())