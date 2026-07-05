# Writing LMS

수능 국어 **비문학(독서) 지문**을 **텍스트 또는 이미지**로 입력받아, 고등학생 대상의
**첨삭 · 자기주도학습 프로그램**을 생성하는 LMS 백엔드.

## 무엇을 하나

입력된 비문학 지문을 분석해 다음 학습 산출물을 만든다.

1. **문단별 중심 문장** — 각 문단의 핵심 주장/정의
2. **논리 구조 요약** — 핵심 화제 + 서론·본론·결론
3. **어휘 암기장** — 고난도 어휘의 사전적 정의 + 문맥적 의미

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

| 변수                          | 기본값                                                              | 설명                                     |
| ----------------------------- | ------------------------------------------------------------------- | ---------------------------------------- |
| `ENV`                         | `development`                                                       | 실행 환경 (development/local/production) |
| `DATABASE_URL`                | `postgresql+psycopg://postgres:postgres@localhost:5432/writing_lms` | SQLAlchemy 비동기 DSN                    |
| `JWT_SECRET`                  | (개발용 기본값)                                                     | **운영에서 반드시 교체**                 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`                                                              | 액세스 토큰 만료(분)                     |
| `LLM_MODEL`                   | `openai:gpt-4o-mini`                                                | `init_chat_model` "provider:model" 규격  |
| `LLM_TEMPERATURE`             | `0.3`                                                               | 분석 생성 온도                           |
| `OCR_BACKEND`                 | `stub`                                                              | OCR 백엔드 식별자                        |
| `CORS_ORIGINS`                | `*`                                                                 | 콤마 구분 허용 오리진                    |

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

| 메서드 | 경로                     | 설명                          |
| ------ | ------------------------ | ----------------------------- |
| POST   | `/auth/register`         | 회원가입                      |
| POST   | `/auth/login`            | 로그인(JWT 발급, OAuth2 form) |
| GET    | `/auth/me`               | 현재 사용자                   |
| POST   | `/writing/analyze`       | 지문 텍스트 → 구조화 분석     |
| POST   | `/writing/ocr`           | 이미지 → 텍스트(OCR)          |
| POST   | `/writing/analyze-image` | 이미지 → OCR → 분석           |

## 프로젝트 구조

```
main.py                    # FastAPI 앱 엔트리
src/app/
  shared/                  # 공용 초기화(config·db·logging·middleware·exceptions·init)
  auth/                    # 로컬 JWT 인증
  user/                    # User 모델/스키마
  writing/                 # 비문학 분석(prompt·schema·analyze·router)
  ocr/                     # OCR 교체 가능 백엔드(인터페이스·팩토리·stub)
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
