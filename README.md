# Writing LMS

수능 국어 **비문학(독서) 지문**을 **텍스트·이미지·PDF**로 입력받아, 고등학생 대상의
**첨삭 · 자기주도학습 프로그램**을 생성하는 LMS 백엔드.

## 무엇을 하나

입력된 비문학 지문을 분석해 다음 학습 산출물을 만든다.

1. **문단별 중심 문장** — 각 문단의 핵심 주장/정의
2. **논리 구조 요약** — 핵심 화제 + 논리 구조 유형 + 서론·본론·결론
3. **어휘 암기장** — 고난도 어휘의 사전적 정의 + 문맥적 의미

분야마다 글 구조가 다른 점을 반영해, 지문을 **6개 도메인(인문/사회/경제/과학/기술/예술)**으로
자동 분류하고 도메인별로 튜닝된 프롬프트(분석 렌즈)로 분석한다. 또한 바로 업로드해 분석하는
방식뿐 아니라, **대화를 이어가다 파일을 올리거나 결과를 수정**하는 human-in-the-loop 흐름을
지원한다(분석 초안 → 리뷰 게이트 → 승인/수정).

향후: 첨삭 피드백, 문제 생성, 학습 자료(PPTX 등) 출력.

## 기술 스택

- **언어/도구**: Python 3.13+, [`uv`](https://docs.astral.sh/uv/), Makefile
- **웹**: FastAPI + uvicorn (API 문서: Scalar `/scalar`, `/openapi.yaml`)
- **오케스트레이션**: LangGraph (동적 StateGraph, Postgres 체크포인팅, human-in-the-loop, SSE)
- **LLM**: LangChain `init_chat_model` (프로바이더 교체 가능 — `LLM_MODEL`)
- **DB**: SQLAlchemy(async) + PostgreSQL, Alembic _(예정)_
- **인증**: 로컬 JWT(HS256) + bcrypt
- **문서/이미지**: pymupdf, python-pptx, OCR(교체 가능 백엔드)
- **품질**: Ruff, mypy, pytest, LangSmith eval

## 시작하기

### 요구 사항

- Python 3.13+
- `uv` (패키지·실행)
- PostgreSQL (인증/파이프라인 등 DB 기능 사용 시)

### 설치

```bash
make install        # uv sync
```

### 환경 변수

`.env`(개발) 또는 `.env.local`(로컬)에 설정한다. 주요 값:

| 변수                          | 기본값                                                              | 설명                                          |
| ----------------------------- | ------------------------------------------------------------------- | --------------------------------------------- |
| `ENV`                         | `development`                                                       | 실행 환경 (development/local/production)      |
| `DATABASE_URL`                | `postgresql+psycopg://postgres:postgres@localhost:5432/writing_lms` | SQLAlchemy 비동기 DSN                         |
| `JWT_SECRET`                  | (개발용 기본값)                                                     | **운영에서 반드시 교체**                      |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`                                                              | 액세스 토큰 만료(분)                          |
| `LLM_MODEL`                   | `openai:gpt-4o-mini`                                                | `init_chat_model` "provider:model" 규격       |
| `LLM_TEMPERATURE`             | `0.3`                                                               | 분석 생성 온도                                |
| `OCR_BACKEND`                 | `stub`                                                              | OCR 백엔드 식별자                             |
| `AGENT_CHECKPOINTER`          | `memory`                                                            | 대화 에이전트 체크포인터(`memory`/`postgres`) |
| `OLLAMA_HOST`                 | `http://localhost:11434`                                            | 로컬 LLM(ollama) base_url                     |
| `CORS_ORIGINS`                | `*`                                                                 | 콤마 구분 허용 오리진                         |

> 라이브 LLM 실행에는 선택한 프로바이더의 API 키(예: `OPENAI_API_KEY`)가 필요하다.

### 실행

```bash
make dev            # FastAPI 개발 서버 (.env) — http://localhost:8000
make local          # FastAPI 로컬 (.env.local)
make graph-dev      # LangGraph dev 서버 — :2024
```

- Swagger UI: `http://localhost:8000/docs`
- Scalar: `http://localhost:8000/scalar`

FastAPI 서버(:8000)와 LangGraph 서버(:2024)는 별개로 뜬다.

## API 개요

| 메서드 | 경로                     | 설명                                       |
| ------ | ------------------------ | ------------------------------------------ |
| POST   | `/auth/register`         | 회원가입                                   |
| POST   | `/auth/login`            | 로그인(JWT 발급, OAuth2 form)              |
| GET    | `/auth/me`               | 현재 사용자                                |
| POST   | `/writing/analyze`       | 지문 텍스트 → 도메인 분류 → 구조화 분석    |
| POST   | `/writing/ocr`           | 이미지 → 텍스트(OCR)                       |
| POST   | `/writing/analyze-image` | 이미지 → OCR → 분석                        |
| POST   | `/writing/pdf`           | PDF → 텍스트(텍스트 레이어/스캔 OCR 폴백)  |
| POST   | `/writing/analyze-pdf`   | PDF → 텍스트 추출 → 분석                   |
| POST   | `/writing/chat`          | 대화형 분석: 메시지 전송(신규/기존 스레드) |
| POST   | `/writing/chat/upload`   | 대화 중 파일 업로드(이미지/PDF) → 분석     |
| POST   | `/writing/chat/resume`   | 리뷰 게이트 재개(승인/수정 지시)           |
| GET    | `/llm/health`            | LLM(ollama) 서버·모델 준비 점검            |

> `/writing/analyze`·`/analyze-image`·`/analyze-pdf` 응답은 `AnalyzeResponse`
> (분석 결과 + 적용된 도메인 분류). 대화형 엔드포인트는 `AgentTurnResponse`
> (`status`: 리뷰 대기 `interrupted` / 턴 종료 `completed`)를 반환한다.

## 프로젝트 구조

```
main.py                    # FastAPI 앱 엔트리
src/app/
  shared/                  # 공용 초기화(config·db·logging·middleware·exceptions·init)
  auth/                    # 로컬 JWT 인증
  user/                    # User 모델/스키마
  writing/                 # 비문학 분석 도메인(핵심 슬라이스)
    domain.py              #   6분류 도메인 + 분류기(classify_domain)
    domain_prompts.py      #   도메인별 분석 렌즈 + 프롬프트 합성
    analyze.py             #   run_analysis(분류→렌즈→분석)·revise_analysis
    pdf.py                 #   PDF 텍스트 추출(레이어 우선, 스캔 OCR 폴백)
    agent.py               #   대화형 ReAct 에이전트 + 리뷰 게이트(HITL)
    prompt.py·schema.py·router.py
  ocr/                     # OCR 교체 가능 백엔드(인터페이스·팩토리·stub)
  llm/                     # LLM 공용 팩토리 + ollama 연동/health
  doc/                     # Document 모델/서비스/파이프라인
  core/langgraph/          # LangGraph 전용 앱
  models.py                # 모델 매퍼 레지스트리
```

## 개발

```bash
make lint           # ruff (변경 파일)
make format         # ruff format
make test           # pytest
```

- 코딩 규칙은 [`.claude/CLAUDE.md`](.claude/CLAUDE.md) 참고 (엄격한 Ruff 룰셋: 타입 어노테이션 필수,
  `print` 금지, `from __future__ import annotations` 등).

## 상태

초기 개발 단계다. 완료·진행 상황은 [`CHANGELOG.md`](CHANGELOG.md)와
[`.claude/CLAUDE.md`](.claude/CLAUDE.md)의 "현재 상태(WIP)"를 참고.
