from app.models.ai import AI
from app.repositories.base_repository import get_database
class AiRepository:

    @staticmethod
    async def get_ai_instruction() -> AI:
        return await AI.find_one()

    @staticmethod
    async def update_ai_instruction(instructions: str, voice: str) -> AI:
        db = get_database()
        await db.drop_collection("AI")
        ai_obj = await AI.find_one()
        if not ai_obj:
            ai_obj = AI(instructions=instructions, voice=voice)
        else:
            ai_obj.instructions = instructions
            ai_obj.voice = voice
        await ai_obj.save()
        return ai_obj
