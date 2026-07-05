# Changelog

이 프로젝트의 주요 변경 사항을 기록한다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
버전 관리는 [유의적 버전](https://semver.org/lang/ko/)을 따른다.

## [Unreleased]

초기 스캐폴드 이후 백엔드 기반 레이어를 구축하는 단계. 아직 릴리스/태그 없음.

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

### 알려진 제약 / 예정
- Alembic 마이그레이션·실 DB 통합 미완(인증 DB happy-path는 Postgres 필요).
- LLM 프로바이더 미확정(설정으로 교체). 라이브 실행에 프로바이더 키 필요.
- OCR 실제 백엔드 미선택(스캐폴드까지). 추천 후보: RapidOCR.
- `/writing/*` 엔드포인트는 v1 공개 상태(추후 `CurrentUser`로 보호 예정).
- `doc/api.py`·`doc/pipeline_service.py`는 미정의 심볼 다수로 아직 미배선(WIP).

[Unreleased]: https://example.com/writing-lms/compare/HEAD
