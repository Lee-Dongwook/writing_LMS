"""모든 SQLAlchemy 모델을 한 곳에서 import해 매퍼 레지스트리에 등록한다.

관계(relationship)가 서로를 문자열로 참조하므로, 매퍼 설정 전에 모든 모델이
import되어 있어야 한다. 앱 부팅/Alembic/테스트에서 이 모듈만 import하면 된다.
"""

from __future__ import annotations

from src.app.doc.model import Document
from src.app.user.model import User

__all__ = ["Document", "User"]
