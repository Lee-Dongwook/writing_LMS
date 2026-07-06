from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, create_model

# `Document.inputs`(JSONB)의 각 요소는 동적 폼 필드 정의다. 예:
#   {"key": "passage", "type": "textarea", "required": true, "label": "지문"}
#
# 요소 `type`을 파이썬 타입으로 매핑해 문서별 검증용 Pydantic 모델을 생성한다.
# 파일/이미지 요소는 v1에서 텍스트 우선 정책상 임의 구조(dict)를 허용한다(후속 처리).

_TYPE_MAP: dict[str, type] = {
    "text": str,
    "string": str,
    "textarea": str,
    "select": str,
    "email": str,
    "number": int,
    "int": int,
    "integer": int,
    "float": float,
    "boolean": bool,
    "checkbox": bool,
    # 파일/이미지: FileInfo 형태의 dict를 그대로 통과(후속 파일 처리에서 해석).
    "file": dict,
    "image": dict,
}


def _element_key(element: dict[str, Any]) -> str | None:
    """요소의 필드 키를 추출한다(`key` 우선, 없으면 `name`)."""
    key = element.get("key") or element.get("name")
    return str(key) if key else None


def create_dynamic_model_from_elements(
    model_name: str,
    elements: list[dict[str, Any]],
) -> type[BaseModel]:
    """폼 요소 정의 리스트로 문서별 검증용 Pydantic 모델을 동적 생성한다.

    - `required`가 참인 필드는 필수, 아니면 `None` 기본값의 선택 필드가 된다.
    - 알 수 없는 `type`은 안전하게 `str`로 취급한다.
    - 키가 없는 요소는 건너뛴다(표시 전용 요소 등).
    """
    fields: dict[str, Any] = {}
    for element in elements or []:
        key = _element_key(element)
        if not key:
            continue

        py_type = _TYPE_MAP.get(str(element.get("type", "text")).lower(), str)
        description = element.get("label") or element.get("description") or ""

        if element.get("required", False):
            fields[key] = (py_type, Field(description=description))
        else:
            fields[key] = (py_type | None, Field(default=None, description=description))

    return create_model(model_name, **fields)
