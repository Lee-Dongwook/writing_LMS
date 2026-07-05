# Writing LMS Makefile
# 환경별 실행을 위한 명령어들

.PHONY: help dev local prod install clean test test-coverage eval eval-baseline eval-quick eval-pr-gate eval-multi eval-agreement eval-report eval-nightly lint format pre-commit

# 기본 명령어 (도움말)
help:
	@echo "🧠 Writing LMS 명령어"
	@echo ""
	@echo "📦 설치 및 설정:"
	@echo "  make install     - 의존성 설치"
	@echo "  make clean       - 캐시 및 임시 파일 정리"
	@echo ""
	@echo "🚀 실행 명령어:"
	@echo "  make dev         - 개발 환경으로 실행 (.env 파일 사용)"
	@echo "  make local       - 로컬 환경으로 실행 (.env.local 파일 사용)"
	@echo "  make prod        - 프로덕션 환경으로 실행"
	@echo ""
	@echo "🛠️  개발 도구:"
	@echo "  make test        - 테스트 실행"
	@echo "  make test-coverage - 테스트 커버리지 측정"
	@echo "  make eval        - LangSmith 평가(full)"
	@echo "  make eval-baseline - LangSmith 기준선(baseline) 갱신"
	@echo "  make eval-quick  - LangSmith 평가(quick)"
	@echo "  make eval-pr-gate - PR 품질 게이트용 quick eval"
	@echo "  make eval-multi  - 다중 evaluator(gpt/claude) eval 실행"
	@echo "  make eval-agreement - evaluator 간 일치도(alpha) 계산"
	@echo "  make eval-report - 최신 eval 리포트 요약 출력"
	@echo "  make eval-nightly - full eval + multi + agreement"
	@echo "  make lint        - 코드 린팅"
	@echo "  make format      - 코드 포매팅"
	@echo "  make pre-commit  - pre-commit 전체 실행"
	@echo ""
	@echo "📊 LangGraph:"
	@echo "  make graph-dev   - LangGraph 개발 서버 실행"
	@echo "  make graph-local - LangGraph 로컬 환경 실행"
	@echo ""
	@echo "🗄️  데이터베이스 마이그레이션:"
	@echo "  make migrate-dev     - 개발 환경 DB 마이그레이션 (.env)"
	@echo "  make migrate-local   - 로컬 환경 DB 마이그레이션 (.env.local)"
	@echo "  make revision-dev    - 개발 환경 새 마이그레이션 생성"
	@echo "  make revision-local  - 로컬 환경 새 마이그레이션 생성"
	@echo "  make downgrade-dev   - 개발 환경 마이그레이션 롤백"
	@echo "  make downgrade-local - 로컬 환경 마이그레이션 롤백"
	@echo "  make current-dev     - 개발 환경 마이그레이션 상태 확인"
	@echo "  make current-local   - 로컬 환경 마이그레이션 상태 확인"
	@echo "  make history         - 마이그레이션 히스토리 확인"

# 의존성 설치
install:
	@echo "📦 의존성 설치 중..."
	uv sync

# 개발 환경 실행 (.env 파일 사용)
dev:
	@echo "🚀 개발 환경으로 서버 시작 (.env 파일 사용)"
	@if [ -f .env ]; then \
		echo "✅ .env 파일 발견"; \
		set -a && . ./.env && set +a && ENV=development uv run python main.py; \
	else \
		echo "⚠️  .env 파일이 없습니다!"; \
		ENV=development uv run python main.py; \
	fi

# 로컬 환경 실행 (.env.local 파일 사용)
local:
	@echo "🏠 로컬 환경으로 서버 시작 (.env.local 파일 사용)"
	@if [ -f .env.local ]; then \
		echo "✅ .env.local 파일 발견"; \
		set -a && . ./.env.local && set +a && ENV=local uv run python main.py; \
	else \
		echo "❌ .env.local 파일이 없습니다!"; \
		echo "💡 .env.local 파일을 생성하거나 'make dev' 명령어를 사용하세요."; \
		exit 1; \
	fi

# 프로덕션 환경 실행
prod:
	@echo "🏭 프로덕션 환경으로 서버 시작"
	ENV=production uv run uvicorn main:app --host 0.0.0.0 --port 8000

# LangGraph 개발 서버 (.env 파일 사용)
graph-dev:
	@echo "📊 LangGraph 개발 서버 시작 (.env 파일 사용)"
	@if [ -f .env ]; then \
		echo "✅ .env 파일 발견"; \
	set -a && . ./.env && set +a && ENV=development BG_JOB_ISOLATED_LOOPS=true uv run langgraph dev --allow-blocking --port $${PORT:-2024}; \
	else \
		echo "⚠️  .env 파일이 없습니다!"; \
		ENV=development uv run langgraph dev --port $${PORT:-2024}; \
	fi

# LangGraph 로컬 환경 (.env.local 파일 사용)
graph-local:
	@echo "📊 LangGraph 로컬 환경 서버 시작 (.env.local 파일 사용)"
	@if [ -f .env.local ]; then \
		echo "✅ .env.local 파일 발견"; \
		set -a && . ./.env.local && set +a && ENV=local BG_JOB_ISOLATED_LOOPS=true uv run langgraph dev --allow-blocking $${PORT:-2024}; \
	else \
		echo "❌ .env.local 파일이 없습니다!"; \
		echo "💡 .env.local 파일을 생성하거나 'make graph-dev' 명령어를 사용하세요."; \
		exit 1; \
	fi

# Define a variable for Python and notebook files.
MAIN_BRANCH ?= develop
BRANCH_BASE := $(shell git merge-base origin/$(MAIN_BRANCH) HEAD 2>/dev/null || echo origin/$(MAIN_BRANCH))

# Default file types to check if FILES is not provided
FILES ?= "*.py" "*.ipynb"

# 1. Neutralize dangerous characters by replacing them with spaces.
# This prevents command injection while keeping file paths separate.
# Characters to neutralize: " ' ( ) ; & | > < ` $
_UNSAFE_CHARS := " ' ( ) ; & | > < ` $$
_CLEANED := $(FILES)
$(foreach char,$(_UNSAFE_CHARS),$(eval _CLEANED := $(subst $(char), ,$(_CLEANED))))

CLEAN_FILES = $(_CLEANED)
$(info - CLEAN_FILES is "$(CLEAN_FILES)")
# 2. Re-apply single quotes to each pattern. If empty, use defaults to avoid full-repo scan.
SAFE_FILES = $(if $(CLEAN_FILES),$(foreach f,$(CLEAN_FILES),'$(f)'),"*.py" "*.ipynb")

# Helper to get staged files or fall back to branch diff using dynamic pathspecs
GET_STAGED_FILES = $(shell git diff --cached --name-only --diff-filter=ACMR -- $(SAFE_FILES) ':!alembic' 2>/dev/null)
GET_CHANGED_FILES = $(shell git diff --name-only --diff-filter=ACMR $(BRANCH_BASE) HEAD -- $(SAFE_FILES) ':!alembic' 2>/dev/null)
GET_PYTHON_FILES = $(or $(GET_STAGED_FILES),$(GET_CHANGED_FILES))

PYTHON_FILES=src
MYPY_CACHE=.mypy_cache
lint format check-diff check-fix type pre-commit: PYTHON_FILES=$(GET_PYTHON_FILES)
lint_diff format_diff: PYTHON_FILES=$(GET_PYTHON_FILES)
lint_package: PYTHON_FILES=src
lint_all format_all: PYTHON_FILES=.
lint_tests: PYTHON_FILES=tests
lint_tests: MYPY_CACHE=.mypy_cache_test
type_package: PYTHON_FILES=src


# 테스트 실행
test:
	@echo "🧪 테스트 실행 중..."
	uv run pytest tests/ -v

# 테스트 커버리지 측정
test-coverage:
	@echo "📊 테스트 커버리지 측정 중..."
	uv run pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=70

# LangSmith 평가 (full)
eval:
	@echo "🧪 LangSmith eval 실행 중..."
	EVAL_ENV=$${EVAL_ENV:-dev} EVAL_DATASET_FILE=$${EVAL_DATASET_FILE:-chatbot_dataset_v3.csv} LANGSMITH_TEST_CACHE=tests/evals/cassettes uv run pytest tests/evals -v -m langsmith

# LangSmith baseline 생성/갱신
eval-baseline:
	@echo "🧱 LangSmith eval baseline 갱신 중..."
	EVAL_SET_BASELINE=1 EVAL_ENV=$${EVAL_ENV:-dev} EVAL_DATASET_FILE=$${EVAL_DATASET_FILE:-chatbot_dataset_v3.csv} LANGSMITH_TEST_CACHE=tests/evals/cassettes uv run pytest tests/evals -v -m langsmith

# LangSmith 평가(quick) 공통 실행 명령
_EVAL_QUICK_CMD = EVAL_DATASET_FILE=$${EVAL_DATASET_FILE:-chatbot_dataset_v2.csv} EVAL_CASE_LIMIT=$${EVAL_CASE_LIMIT:-10} LANGSMITH_TEST_CACHE=tests/evals/cassettes uv run pytest tests/evals -v -m langsmith -k "test_link_category_evaluation or test_final_response_validation"

# LangSmith 평가 (quick)
eval-quick:
	@echo "⚡ LangSmith eval quick 실행 중..."
	EVAL_ENV=$${EVAL_ENV:-dev} $(_EVAL_QUICK_CMD)

# PR 게이트용 quick eval
eval-pr-gate:
	@echo "🚦 PR 품질 게이트용 eval 실행 중..."
	EVAL_ENV=staging $(_EVAL_QUICK_CMD)

# LangSmith 다중 evaluator 실행
eval-multi:
	@echo "🔁 다중 evaluator eval 실행 중..."
	EVAL_ENV=$${EVAL_ENV:-dev} EVAL_DATASET_FILE=$${EVAL_DATASET_FILE:-chatbot_dataset_v3.csv} EVAL_CASE_LIMIT=$${EVAL_CASE_LIMIT:-20} EVAL_AGREEMENT_MODELS=$${EVAL_AGREEMENT_MODELS:-gpt-4o-mini,gpt-4o,claude-3-5-sonnet} LANGSMITH_TEST_CACHE=$${LANGSMITH_TEST_CACHE:-tests/evals/cassettes} uv run python tests/evals/run_multi_eval.py

# evaluator 간 일치도 계산
eval-agreement:
	@echo "📐 evaluator 간 일치도(alpha) 계산 중..."
	uv run python tests/evals/run_agreement.py

# 최신 eval 리포트 요약
eval-report:
	@echo "🧾 eval 리포트 요약 출력 중..."
	uv run python tests/evals/render_report.py

# Nightly eval: full + multi + agreement
eval-nightly:
	@echo "🌙 Nightly eval 파이프라인 실행 중..."
	$(MAKE) eval EVAL_ENV=staging EVAL_DATASET_FILE=chatbot_dataset_v3.csv
	$(MAKE) eval-multi EVAL_ENV=staging EVAL_DATASET_FILE=chatbot_dataset_v3.csv EVAL_CASE_LIMIT=20
	$(MAKE) eval-agreement
# 코드 린팅
lint lint_diff lint_package lint_tests lint_all:
	@echo "branch = $(BRANCH_BASE)"
	@echo "🔍 코드 린팅 중..." $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || uv run --all-groups ruff check $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || uv run --all-groups ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" != "" ] && mkdir -p $(MYPY_CACHE) && uv run --all-groups mypy $(PYTHON_FILES) --cache-dir $(MYPY_CACHE)

# 코드 포매팅
format format_diff format_all:
	@echo "✨ 코드 포매팅 중..."
	[ "$(PYTHON_FILES)" = "" ] || uv run --all-groups ruff format $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || uv run --all-groups ruff check --fix $(PYTHON_FILES)

check-diff:
	@echo "🔍 포매팅/린트 위반 확인 중..."
	[ "$(PYTHON_FILES)" = "" ] || uv run --all-groups ruff format --diff $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || uv run --all-groups ruff check --diff $(PYTHON_FILES)

check-fix:
	@echo "✨ check --fix..."
	[ "$(PYTHON_FILES)" = "" ] || uv run --all-groups ruff check --fix $(PYTHON_FILES)

type type_package:
	[ "$(PYTHON_FILES)" != "" ] && mkdir -p $(MYPY_CACHE) && uv run --all-groups mypy $(PYTHON_FILES) --cache-dir $(MYPY_CACHE) || true

# 캐시 및 임시 파일 정리
clean:
	@echo "🧹 정리 중..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ 정리 완료"

# 데이터베이스 마이그레이션 - 개발 환경 (.env)
migrate-dev:
	@echo "🗄️  개발 환경 DB 마이그레이션 실행 (.env 사용)"
	@if [ -f .env ]; then \
		set -a && . ./.env && set +a && uv run alembic upgrade head; \
	else \
		echo "❌ .env 파일이 없습니다!"; \
		exit 1; \
	fi

# 데이터베이스 마이그레이션 - 로컬 환경 (.env.local)
migrate-local:
	@echo "🗄️  로컬 환경 DB 마이그레이션 실행 (.env.local 사용)"
	@if [ -f .env.local ]; then \
		set -a && . ./.env.local && set +a && uv run alembic upgrade head; \
	else \
		echo "❌ .env.local 파일이 없습니다!"; \
		echo "💡 .env.local 파일을 먼저 생성하세요."; \
		exit 1; \
	fi

# database migration for pytest (.env.pytest)
migrate-pytest:
	@echo "🗄️  pytest 환경 DB 마이그레이션 실행 (.env.pytest 사용)"
	@if [ -f .env.pytest ]; then \
		set -a && . ./.env.pytest && set +a && uv run alembic upgrade head; \
	else \
		echo "❌ .env.pytest 파일이 없습니다!"; \
		echo "💡 .env.pytest 파일을 먼저 생성하세요."; \
		exit 1; \
	fi

# 새 마이그레이션 생성 - 개발 환경
revision-dev:
	@echo "📝 개발 환경 새 마이그레이션 생성 (.env 사용)"
	@if [ -z "$(m)" ]; then \
		echo "❌ 마이그레이션 메시지가 필요합니다!"; \
		echo "💡 사용법: make revision-dev m='마이그레이션 메시지'"; \
		exit 1; \
	fi
	@if [ -f .env ]; then \
		set -a && . ./.env && set +a && uv run alembic revision --autogenerate -m "$(m)"; \
	else \
		echo "❌ .env 파일이 없습니다!"; \
		exit 1; \
	fi

# 새 마이그레이션 생성 - 로컬 환경
revision-local:
	@echo "📝 로컬 환경 새 마이그레이션 생성 (.env.local 사용)"
	@if [ -z "$(m)" ]; then \
		echo "❌ 마이그레이션 메시지가 필요합니다!"; \
		echo "💡 사용법: make revision-local m='마이그레이션 메시지'"; \
		exit 1; \
	fi
	@if [ -f .env.local ]; then \
		set -a && . ./.env.local && set +a && uv run alembic revision --autogenerate -m "$(m)"; \
	else \
		echo "❌ .env.local 파일이 없습니다!"; \
		exit 1; \
	fi

# 새 마이그레이션 생성 - pytest
revision-pytest:
	@echo "📝 로컬 환경 새 마이그레이션 생성 (.env.pytest 사용)"
	@if [ -z "$(m)" ]; then \
		echo "❌ 마이그레이션 메시지가 필요합니다!"; \
		echo "💡 사용법: make revision-pytest m='마이그레이션 메시지'"; \
		exit 1; \
	fi
	@if [ -f .env.pytest ]; then \
		set -a && . ./.env.pytest && set +a && uv run alembic revision --autogenerate -m "$(m)"; \
	else \
		echo "❌ .env.pytest 파일이 없습니다!"; \
		exit 1; \
	fi

# 마이그레이션 롤백 - 개발 환경
downgrade-dev:
	@echo "⏪ 개발 환경 마이그레이션 롤백 (.env 사용)"
	@if [ -f .env ]; then \
		set -a && . ./.env && set +a && uv run alembic downgrade -1; \
	else \
		echo "❌ .env 파일이 없습니다!"; \
		exit 1; \
	fi

# 마이그레이션 롤백 - 로컬 환경
downgrade-local:
	@echo "⏪ 로컬 환경 마이그레이션 롤백 (.env.local 사용)"
	@if [ -f .env.local ]; then \
		set -a && . ./.env.local && set +a && uv run alembic downgrade -1; \
	else \
		echo "❌ .env.local 파일이 없습니다!"; \
		exit 1; \
	fi

# 마이그레이션 롤백 - pytest
downgrade-pytest:
	@echo "⏪ 로컬 환경 마이그레이션 롤백 (.env.pytest 사용)"
	@if [ -f .env.pytest ]; then \
		set -a && . ./.env.pytest && set +a && uv run alembic downgrade -1; \
	else \
		echo "❌ .env.pytest 파일이 없습니다!"; \
		exit 1; \
	fi

# 마이그레이션 히스토리 확인
history:
	@echo "📜 마이그레이션 히스토리 확인"
	uv run alembic history

# 현재 마이그레이션 상태 확인 - 개발 환경
current-dev:
	@echo "🔍 개발 환경 현재 마이그레이션 상태 (.env 사용)"
	@if [ -f .env ]; then \
		set -a && . ./.env && set +a && uv run alembic current; \
	else \
		echo "❌ .env 파일이 없습니다!"; \
		exit 1; \
	fi

# 현재 마이그레이션 상태 확인 - 로컬 환경
current-local:
	@echo "🔍 로컬 환경 현재 마이그레이션 상태 (.env.local 사용)"
	@if [ -f .env.local ]; then \
		set -a && . ./.env.local && set +a && uv run alembic current; \
	else \
		echo "❌ .env.local 파일이 없습니다!"; \
		exit 1; \
	fi

# 현재 마이그레이션 상태 확인 - pytest
current-pytest:
	@echo "🔍 로컬 환경 현재 마이그레이션 상태 (.env.pytest 사용)"
	@if [ -f .env.pytest ]; then \
		set -a && . ./.env.pytest && set +a && uv run alembic current; \
	else \
		echo "❌ .env.pytest 파일이 없습니다!"; \
		exit 1; \
	fi

