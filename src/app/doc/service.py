from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from src.app.doc.model import Document

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_doc_by_uuid(
    doc_uuid: str,
    user_uuid: str,
    db: AsyncSession,
) -> Document | None:
    """소유자(user_uuid)에 속한 문서를 uuid로 조회한다.

    존재하지 않거나 소유자가 다르면 None을 반환한다.
    """
    stmt = select(Document).where(
        Document.uuid == doc_uuid,
        Document.user_uuid == user_uuid,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
