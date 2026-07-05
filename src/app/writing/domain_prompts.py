from __future__ import annotations

import textwrap

from src.app.writing.domain import Domain
from src.app.writing.prompt import analysis_system_prompt

# 도메인별 '분석 렌즈'. base 프롬프트(공통 제약·출력 관점)에 덧붙는 fragment로,
# 주로 '요약의 본론 전개 방식'과 '어휘 선정 기준'을 그 분야의 글 구조에 맞게 튜닝한다.
# 중심 문장 추출 규칙·제약 사항은 base에서 공유하므로 여기서 반복하지 않는다.

_DOMAIN_LENS: dict[Domain, str] = {
    Domain.HUMANITIES: textwrap.dedent("""\
        이 지문은 인문(철학·윤리·역사·논리) 분야입니다.
        - 전개: 핵심 개념의 '정의'와 사상가·학파 간 '관점 대립', 시대에 따른 통시적 변화에 주목하세요.
          요약에서는 어떤 개념을 어떻게 규정하고, 어떤 입장이 무엇에 반대/보완하는지를 드러내세요.
        - 어휘: 추상 개념어와 한자어, 철학·논리 용어를 우선 선정하세요."""),
    Domain.SOCIAL: textwrap.dedent("""\
        이 지문은 사회(법·정치·행정·문화) 분야입니다.
        - 전개: 제도·규범의 '요건과 효과', 개념 간 위계와 분류, 원칙과 예외에 주목하세요.
          요약에서는 어떤 조건에서 어떤 결과·권리·의무가 발생하는지를 드러내세요.
        - 어휘: 법률·제도·행정 용어와 사회과학 개념어를 우선 선정하세요."""),
    Domain.ECONOMICS: textwrap.dedent("""\
        이 지문은 경제(경제 이론·금융·시장) 분야입니다.
        - 전개: 변수 간 '인과 관계'와 조건부 변화(증가/감소, 균형 이동)에 주목하세요.
          요약에서는 무엇이 무엇에 어떤 방향으로 영향을 주는지(모형)를 드러내세요.
        - 어휘: 계량·이론 용어와 지표·제도 용어를 우선 선정하세요."""),
    Domain.SCIENCE: textwrap.dedent("""\
        이 지문은 과학(물리·화학·생명·지구과학) 분야입니다.
        - 전개: 자연 현상의 '원리와 메커니즘', 과정의 단계(원인→과정→결과)에 주목하세요.
          요약에서는 어떤 조건에서 어떤 과정을 거쳐 어떤 현상이 일어나는지를 드러내세요.
        - 어휘: 전문 용어, 단위·현상어, 실험·측정 개념어를 우선 선정하세요."""),
    Domain.TECHNOLOGY: textwrap.dedent("""\
        이 지문은 기술(공학·정보·기술 응용) 분야입니다.
        - 전개: 장치·시스템의 '작동 원리'와 그것이 실제로 '적용·구현'되는 과정에 주목하세요.
          요약에서는 어떤 원리가 어떤 구조/절차로 문제를 해결하는지를 드러내세요.
        - 어휘: 공학·정보 전문 용어와 구성 요소·기능 용어를 우선 선정하세요."""),
    Domain.ARTS: textwrap.dedent("""\
        이 지문은 예술(미학·음악·미술·건축) 분야입니다.
        - 전개: 사조·양식의 특징과 '기법', 미적 개념 간 '대비'에 주목하세요.
          요약에서는 어떤 미적 지향이 어떤 기법으로 구현되고 무엇과 대비되는지를 드러내세요.
        - 어휘: 미학·양식·기법 용어와 비평 개념어를 우선 선정하세요."""),
}


def compose_system_prompt(domain: Domain | None = None) -> str:
    """base 분석 프롬프트에 도메인 렌즈를 합성한다.

    `domain`이 None이면(저신뢰/미분류) base 프롬프트만 반환한다(generalist 폴백).
    """
    if domain is None:
        return analysis_system_prompt
    lens = _DOMAIN_LENS[domain].rstrip()
    return f"{analysis_system_prompt}\n\n[도메인별 분석 렌즈]\n{lens}"
