# Writing LMS — FastAPI 앱 이미지 (uv 기반, Python 3.13)
# 루트에 build-system이 없어 프로젝트 자체는 패키지로 설치하지 않는다.
# 의존성만 .venv에 설치하고, 소스는 sys.path=리포 루트 기준으로 실행한다.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    ENV=production \
    TOKENIZERS_PARALLELISM=false \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 1) 의존성만 먼저 설치(레이어 캐시). 잠금 파일 고정(--frozen).
#    readme 메타 참조 때문에 README.md도 함께 복사한다.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 2) 애플리케이션 소스
COPY main.py ./
COPY src ./src

EXPOSE 8000

# ENV=production → main.py가 0.0.0.0:8000로 uvicorn 기동
CMD ["python", "main.py"]
