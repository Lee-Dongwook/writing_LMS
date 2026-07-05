from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from src.app.writing.domain import DomainClassification

# 스키마의 Field 설명은 LLM structured output 가이드로도 사용되므로 한국어로 명확히 쓴다.


class StructureType(str, Enum):
    """지문 본론의 논리 전개 유형. 도메인과 독립적으로 글의 구조 신호를 담는다."""

    DEFINITION_EXAMPLE = "정의-예시"
    CAUSATION = "인과"
    CONTRAST = "대조"
    CHRONOLOGICAL = "통시"
    PROBLEM_SOLUTION = "문제-해결"
    CLASSIFICATION = "분류-위계"
    PROCESS = "과정-절차"


class ParagraphKeySentence(BaseModel):
    """문단별 중심 문장."""

    paragraph: int = Field(description="문단 번호(1부터 시작).")
    key_sentence: str = Field(
        description="해당 문단의 핵심 주장/정의가 담긴 중심 문장. 예시나 부연이 아닌 논지.",
    )


class Summary(BaseModel):
    """지문 전체의 논리 구조 요약."""

    topic: str = Field(description="지문이 다루는 가장 중요한 핵심 화제.")
    structure_type: StructureType = Field(
        description="본론의 논리 전개 유형. 지문 구조에 가장 부합하는 하나를 고른다.",
    )
    intro: str = Field(description="서론(도입부)에서 제시된 문제의식이나 배경.")
    body: str = Field(description="본론(전개부)의 핵심 내용. 인과/대립 구조가 드러나게.")
    conclusion: str = Field(description="결론(마무리)에서의 정리나 함의.")


class VocabItem(BaseModel):
    """어휘 암기장 항목."""

    word: str = Field(description="고난도 어휘/한자어/핵심 개념어.")
    dictionary_meaning: str = Field(
        description="표준국어대사전 기준 사전적 정의를 학생이 이해하기 쉽게 서술.",
    )
    context_meaning: str = Field(description="지문 내 문맥에서의 쓰임새 및 쉬운 풀이.")


class PassageAnalysis(BaseModel):
    """수능 비문학 지문 분석 결과."""

    key_sentences: list[ParagraphKeySentence] = Field(
        description="문단 순서대로의 중심 문장 목록.",
    )
    summary: Summary = Field(description="지문 전체 요약.")
    vocabulary: list[VocabItem] = Field(
        description="지문 속 고난도 어휘 5~7개의 암기 리스트.",
    )


class AnalyzeRequest(BaseModel):
    """지문 분석 요청."""

    passage: str = Field(min_length=1, description="분석할 수능 비문학 지문 원문(텍스트).")


class AnalyzeResponse(BaseModel):
    """도메인 분류 + 지문 분석 결과.

    어떤 도메인 렌즈로 분석했는지 클라이언트가 알 수 있도록 분류 결과를 함께 담는다.
    """

    classification: DomainClassification = Field(description="지문 도메인 분류 결과.")
    analysis: PassageAnalysis = Field(description="도메인 렌즈로 튜닝된 분석 결과.")
