"""
ai/ — OpenAI GPT-5.4 기반 LLM 파이프라인
==========================================

주제 선별, 본문 생성, 스핀오프 추출을 OpenAI API 로 수행합니다.
"""

from .selector import select_best_topic
from .generator import generate_newsletter
from .spinoff import generate_spinoffs

__all__ = ["select_best_topic", "generate_newsletter", "generate_spinoffs"]
