"""평문 비밀번호의 bcrypt 해시를 출력한다(어드민 자격증명 생성용).

실행: `make hash-password` — 비밀번호를 숨김 입력(getpass)으로 받아 해시만 stdout에 낸다.
출력값을 `.env`의 ADMIN_PASSWORD_HASH 에 넣는다(반드시 작은따옴표로 감쌀 것: bcrypt
해시의 `$` 가 셸/소싱 시 변수로 해석되지 않도록).
"""

from __future__ import annotations

import sys
from getpass import getpass

from src.app.auth.security import hash_password


def _read_password() -> str:
    # 인자로 주면 그대로(비대화형/CI), 없으면 숨김 입력을 2회 받아 확인.
    if len(sys.argv) > 1:
        return sys.argv[1]
    pw = getpass("비밀번호: ")
    if pw != getpass("비밀번호 확인: "):
        sys.exit("비밀번호가 일치하지 않습니다.")
    if not pw:
        sys.exit("빈 비밀번호는 허용되지 않습니다.")
    return pw


def main() -> None:
    # 해시만 출력(파이프/복사 편의). 안내문은 stderr로.
    sys.stderr.write("아래 해시를 .env의 ADMIN_PASSWORD_HASH 에 '작은따옴표'로 넣으세요:\n")
    sys.stdout.write(hash_password(_read_password()) + "\n")


if __name__ == "__main__":
    main()
