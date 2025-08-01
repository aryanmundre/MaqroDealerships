from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
# from maqro_backend.db.models.conversation import Conversation  # Removed - using raw SQL now


async def get_average_agent_response_time(session: AsyncSession) -> float | None:
    stmt = (
        select(func.avg(Conversation.response_time_sec))
        .where(
            Conversation.sender == "agent",
            Conversation.response_time_sec.is_not(None),
        )
    )

    result = await session.execute(stmt)
    avg_value: float | None = result.scalar()
    return avg_value 