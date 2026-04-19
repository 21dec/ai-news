"""
ai/ — Legacy Anthropic API 기반 LLM 경로 (deprecated)
======================================================

이 패키지는 과거 Anthropic API 를 직접 호출하던 시점의 모듈을 보관합니다.
현재 시스템은 `anthropic` 패키지를 의존성에서 제거했으며, LLM 작업은
Claude 스케줄 태스크 세션이 직접 수행합니다.

`anthropic` 모듈이 설치되어 있지 않은 환경에서도 파이프라인의
다른 경로(크롤러·출력·검증·인덱스)가 깨지지 않도록, 여기서는
ImportError 를 조용히 흡수하고 스텁 함수로 대체합니다.
스텁을 직접 호출하면 RuntimeError 로 명시적으로 실패합니다.
"""

try:
    from .selector import select_best_topic
    from .generator import generate_newsletter
    from .spinoff import generate_spinoffs
except ImportError:  # anthropic 패키지 미설치 — 레거시 경로 비활성화
    def _unavailable(*_args, **_kwargs):
        raise RuntimeError(
            "ai/ 레거시 API 경로는 비활성화되어 있습니다. "
            "LLM 작업은 Claude 스케줄 태스크 프롬프트에서 직접 수행하세요."
        )

    select_best_topic = _unavailable
    generate_newsletter = _unavailable
    generate_spinoffs = _unavailable

__all__ = ["select_best_topic", "generate_newsletter", "generate_spinoffs"]
