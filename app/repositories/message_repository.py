



from mailbox import Message


class MessageRepository:
    @staticmethod
    async def create_message(message: Message):
        await message.insert()
    
    @staticmethod
    async def get_message_by_id(message_id: str) -> Message:
        return await Message.objects.get(id=message_id)
    
    @staticmethod
    async def get_messages_by_conversation_id(conversation_id: str) -> List[Message]:
        return await Message.objects.filter(conversation_id=conversation_id)