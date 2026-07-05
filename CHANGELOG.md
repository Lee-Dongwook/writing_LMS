# Changelog

이 프로젝트의 주요 변경 사항을 기록한다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
버전 관리는 [유의적 버전](https://semver.org/lang/ko/)을 따른다.

## [Unreleased]

### Added

**SSE 스트리밍 (`src/app/writing/agent.py`·`router.py`)**

- 대화형 에이전트 턴을 표준 이벤트(`run_started` → `message_chunk`\* → `interrupt` →
  `run_finished` / `run_error`)로 스트리밍. `graph.astream(stream_mode=["messages","updates"])`
  기반: 토큰 단위 `message_chunk`(빈 청크·툴콜 청크 제외), 리뷰 게이트 `__interrupt__`
  감지 → `interrupt` 이벤트, 예외는 스트림 내 `run_error`로 전달 후 정상 종료.
- 스트리밍 엔트리(`astream_message` / `astream_ingest` / `astream_resume`)는 기존
  동기 엔트리(`send_message` / `ingest_passage` / `resume_review`)와 1:1 대응.
- SSE 엔드포인트: `POST /writing/chat/stream`, `/chat/upload/stream`, `/chat/resume/stream`
  (`text/event-stream`, `event:`/`data:` 프레임, UTF-8 `ensure_ascii=False`).

**인증 보호 + 스레드 사용자 귀속 (`src/app/writing/router.py`)**

- `/writing/*` 전 엔드포인트를 `CurrentUser`로 보호(토큰 없으면 401).
- 체크포인터 thread_id를 `{user_uuid}:{client_thread}`로 네임스페이스(`_thread_key`) →
  타 사용자가 같은 식별자를 제시해도 스레드 접근 차단. 응답 `thread_uuid`는 client 값으로 반환.

**Postgres 체크포인터 런타임 배선 (`main.py`·`shared/database.py`·`writing/agent.py`)**

- `AGENT_CHECKPOINTER=postgres`면 FastAPI lifespan에서 커넥션 풀 기반
  `AsyncPostgresSaver`(`checkpointer_pool`)를 열어 대화 에이전트에 주입(`set_active_agent`).
  재시작해도 대화 스레드가 유지된다. `memory`면 기존 인메모리로 동작.

**어드민 계정 + 운영 설정 가드**

- `User.is_admin` + 마이그레이션 `0002`, `CurrentAdmin` 의존성, `UserRead.is_admin` 노출.
- `make seed-admin`(멱등 upsert) — 비밀번호는 bcrypt 해시(`ADMIN_PASSWORD_HASH`)로만 저장.
  해시 생성 `make hash-password`, JWT 시크릿 생성 `make gen-secret`.
- 운영(`ENV=production`)에서 기본 JWT 시크릿/짧은 시크릿/기본 DATABASE_URL이면 부팅 거부.

**인프라 / 운영**

- Docker: `Dockerfile`(uv), `docker-compose.yml`(Postgres 기본 + app/adminer 프로파일),
  Make 타깃(`db-up`/`db-init`/`checkpoint-setup`/`seed-admin` 등).
- Alembic 셋업 + 초기 마이그레이션(`0001` user/document, `0002` is_admin).
- `GET /health` 라이브니스 엔드포인트.
- **테스트 스위트**(`tests/`, DB 없이 동작): 인증 크립토·운영 설정 가드·401 보호·
  스레드 격리·SSE 이벤트·헬스체크. `asyncio_mode=auto`, `pythonpath=["."]`.

### 예정

- OCR 실제 백엔드 선택(현재 stub — 스캔 PDF·이미지 경로에 필요). 추천 후보: RapidOCR.
- `doc/api.py`·`doc/pipeline_service.py`(범용 파이프라인 엔진)는 미정의 심볼 다수로 아직 미배선(WIP).

## [0.2.0] - 2026-07-05

수능 비문학의 분야 다양성에 대응하는 **도메인 라우팅 멀티에이전트**, **PDF 입력**,
**대화형 human-in-the-loop 에이전트**를 추가.

### Added

**도메인 라우팅 멀티에이전트 (`src/app/writing/`)**

- 6분류 도메인 체계(`domain.py`): 인문/사회/경제/과학/기술/예술 + `DomainClassification`
  (도메인/확신도/보조도메인/근거), `classify_domain()` 분류기(temp=0).
- 도메인별 **분석 렌즈**(`domain_prompts.py`): base 프롬프트에 분야별 본론 전개·어휘 선정
  초점을 합성(`compose_system_prompt`). 저신뢰/미분류는 generalist로 폴백.
- `run_analysis()`: 분류 → 렌즈 선택 → 분석 파이프라인. `analyze_passage(domain=...)`로 렌즈 주입.
- `Summary`에 `structure_type`(인과/대조/통시/문제-해결/분류-위계/과정-절차 등 구조 신호) 추가.

**PDF 입력 (`src/app/writing/pdf.py`)**

- `extract_pdf_text()`: 텍스트 레이어 우선 추출(pymupdf, 스레드 오프로드) → 부실하면
  페이지를 이미지로 렌더해 OCR 폴백. 페이지 상한/파싱 오류 일원화(`PdfError`).
- 엔드포인트: `POST /writing/pdf`(추출), `POST /writing/analyze-pdf`(추출→분석).
- 텍스트 레이어 PDF는 OCR 백엔드 없이도 동작(수능 문제지 대부분).

**대화형 human-in-the-loop 에이전트 (`src/app/writing/agent.py`)**

- LangGraph ReAct 에이전트 + **리뷰 게이트**(`interrupt`): 분석/수정 초안을 제시하고
  사용자 승인/수정 지시를 받아 재개(`Command(resume=...)`).
- 툴: `analyze_passage_tool`(분류→렌즈→분석), `revise_analysis_tool`(초안 부분 수정).
  파일은 "수집 경계"에서 추출해 대화(`pending_passage` + `HumanMessage`)로 주입.
- 상태 영속: 인메모리 체크포인터(기본, DB 불필요) ↔ `AGENT_CHECKPOINTER`로 Postgres 전환.
- 엔드포인트: `POST /writing/chat`(메시지), `POST /writing/chat/upload`(이미지/PDF 업로드),
  `POST /writing/chat/resume`(리뷰 재개). 응답 `AgentTurnResponse`(status·reply·interrupt·analysis).

### Changed

- `POST /writing/analyze`·`/analyze-image` 응답이 `AnalyzeResponse`로 변경 — 분석 결과에
  더해 어떤 도메인 렌즈로 분석했는지(`classification`)를 함께 반환.
- `Settings`에 `AGENT_CHECKPOINTER`(기본 `memory`) 추가.

## [0.1.0] - 2026-07-05

초기 스캐폴드 이후 백엔드 기반 레이어를 구축하는 단계.

### Added

**공용 초기화(shared) 레이어**

- `src/app/shared/`: 설정(`Settings`, pydantic-settings), 로깅, 비동기 DB(엔진·세션·`Base`·
  `get_async_db`·`async_context_session`·`get_checkpoint`), 요청 컨텍스트, 미들웨어(요청
  컨텍스트 + CORS), 전역 예외 핸들러, 런타임 초기화(`load_dotenv`·`initialize`).
- `main.py`·`langgraph_app.py`를 shared 심볼로 배선.

**인증 / User 레이어**

- 로컬 JWT(HS256) 인증: bcrypt 비밀번호 해시, 토큰 발급/검증(`security`), `verify_token`
  의존성(`CurrentUser`).
- `User` 모델(DB 테이블) + `UserRead`/`UserCreate` 스키마, 사용자 조회·생성·인증 서비스.
- 엔드포인트: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`.
- `Document`↔`User` FK/relationship, 모델 매퍼 aggregator(`src/app/models.py`).

**핵심 분석 슬라이스**

- `POST /writing/analyze`: 지문 텍스트 → 구조화 분석(`PassageAnalysis` = 중심문장/요약/어휘).
- `analyze_passage()`가 LLM `with_structured_output` 사용. LLM 모델은 `LLM_MODEL` 설정으로
  교체 가능(`init_chat_model` "provider:model" 규격).
- 구조화 출력용 시스템 프롬프트 추가(기존 마크다운 프롬프트 병존).

**OCR (교체 가능 백엔드 스캐폴드)**

- `src/app/ocr/`: `OcrProvider` 인터페이스, 팩토리(`OCR_BACKEND`), 기본 `stub`, `OcrResult`.
- 엔드포인트: `POST /writing/ocr`(이미지→텍스트), `POST /writing/analyze-image`(이미지→OCR→분석).
- 백엔드 미설치 시에도 앱 부팅 가능(호출 시 503으로 설정 유도).

**프로젝트/문서**

- 런타임·개발 의존성을 루트 `pyproject.toml`에 선언하고 `uv sync`로 설치.
- `.claude/CLAUDE.md` 프로젝트 가이드 작성/갱신.
- `README.md` 재작성, `CHANGELOG.md` 추가.

### Changed

- `agents/writing/`(별도 pyproject 서브패키지)를 `src/app/writing/`로 흡수 — 단일 패키지·
  단일 `pyproject.toml`로 통합.
- `doc/model.py`의 `Document`를 shared `Base` 기반으로 정리(`pipeline` 컬럼 추가, timezone-aware
  datetime, User FK/relationship 복원).

### Removed

- macOS/iCloud 동기화가 생성한 중복 파일 제거: `pyproject 2.toml`, `langgraph_app 2.py`.

**LLM 공용 팩토리 / ollama**

- `src/app/llm/`: `get_chat_model()` 프로바이더 공용 팩토리(ollama면 `OLLAMA_HOST`를
  base_url로 주입), `GET /llm/health`(ollama 서버·모델 준비 점검).

[Unreleased]: https://example.com/writing-lms/compare/v0.2.0...HEAD
[0.2.0]: https://example.com/writing-lms/compare/v0.1.0...v0.2.0
[0.1.0]: https://example.com/writing-lms/releases/tag/v0.1.0
