# Simula: 합성 데이터 생성을 메커니즘 디자인으로 재구성한 Google의 프레임워크

2026-04-19

## Summary

Google Research가 공개한 Simula는 합성 데이터셋 생성을 샘플 단위 최적화가 아닌 데이터셋 수준의 자원 배분 문제, 즉 메커니즘 디자인으로 재구성합니다. 커버리지, 복잡도, 품질을 독립 변수로 분리한 뒤 4단계 파이프라인(전역 다양화 → 지역 다양화 → 복잡도 조정 → 이중 검증)으로 도메인당 최대 512K 데이터 포인트를 생성합니다. Gemini 2.5 Flash를 교사 모델, Gemma-3 4B를 학생 모델로 사용하며, 5개 도메인에서 단순 베이스라인 대비 적은 샘플로 더 높은 다운스트림 성능을 달성합니다. ShieldGemma, MedGemma, Android 스캠 탐지 등 프로덕션에 이미 배포되었습니다.

## 본문

### 합성 데이터의 구조적 한계

프라이버시 민감 도메인이나 데이터 희소 영역에서 모델을 학습시키려면 합성 데이터가 필수적입니다. 그러나 기존 접근법은 "더 많은 데이터를 생성하면 된다"는 전제에 머물러 있습니다. 프롬프트 하나로 대량 생성하면 모드 붕괴(mode collapse)가 발생하고, 도메인 커버리지는 편향되며, 난이도 분포는 통제할 수 없습니다. Simula는 이 문제를 개별 샘플이 아닌 데이터셋 전체의 설계 문제로 전환합니다.

### 메커니즘 디자인 관점

Simula의 핵심 통찰은 데이터셋 생성을 자원 배분 문제로 보는 것입니다. 커버리지(어떤 토픽을 다룰 것인가), 복잡도(얼마나 어렵게 만들 것인가), 품질(정답이 맞는가)을 독립적으로 제어 가능한 변수로 분리합니다. 이 세 축을 직교적으로 조합하면, 단일 프롬프트 기반 생성에서 빠지기 쉬운 특정 패턴 과잉 생성을 구조적으로 방지할 수 있습니다.

### 4단계 파이프라인

**1단계 — 전역 다양화(Global Diversification)**: 추론 모델이 재귀적 확장을 통해 깊은 계층형 택소노미를 생성합니다. propose-and-refine 루프에서 비평 모델이 제안을 평가하고 중복을 병합합니다.

**2단계 — 지역 다양화(Local Diversification)**: 1-of-N 메타 프롬프팅으로 각 시나리오의 복수 인스턴스를 생성합니다. 동일 택소노미 노드에서도 서로 다른 구체적 사례가 만들어지므로 모드 붕괴를 억제합니다.

**3단계 — 복잡도 조정(Complexification)**: 메타 프롬프트의 일정 비율에 대해 난이도를 상향 조정합니다. 체스의 Elo 레이팅과 유사한 보정된 복잡도 점수(Calibrated Complexity Scoring)를 적용하여 난이도 분포를 정량 관리합니다.

**4단계 — 이중 검증(Quality Checks)**: 독립적인 두 비평 모델이 정답 정확성을 교차 검증하는 dual-critic 루프를 실행합니다.

### 벤치마크 결과

Simula는 사이버보안(CTIBench), 법률(LEXam), 수학(GSM8k), 다국어(Global MMLU) 등 5개 도메인에서 평가되었습니다. 교사 모델로 Gemini 2.5 Flash, 학생 모델로 Gemma-3 4B를 사용한 결과, 전체 도메인에서 단순 베이스라인을 일관되게 상회합니다. 주목할 점은 복잡도 조정의 효과가 도메인에 따라 상이하다는 것입니다. 수학에서는 높은 복잡도가 정확도를 10% 향상시켰지만, 법률 추론에서는 오히려 성능을 저하시킵니다. 이는 복잡도 축을 도메인 독립적으로 일괄 적용하면 안 된다는 실무적 시사점을 제공합니다.

### 프로덕션 배포 현황

Simula는 이미 Google 내부에서 광범위하게 배포되었습니다. ShieldGemma(안전 분류), FunctionGemma(함수 호출), MedGemma(의료) 등 특수 Gemma 모델의 학습 데이터 생성에 사용되며, Gemini 안전 분류기의 온디바이스·서버사이드 양쪽 학습 데이터의 주 합성 백본입니다. Android 통화 스캠 탐지, Google Messages 스팸 필터링에도 적용됩니다. 논문은 Transactions on Machine Learning Research에 게재되었습니다.

## References

- [https://research.google/blog/designing-synthetic-datasets-for-the-real-world-mechanism-design-and-reasoning-from-first-principles/](https://research.google/blog/designing-synthetic-datasets-for-the-real-world-mechanism-design-and-reasoning-from-first-principles/)
- [https://openreview.net/pdf?id=NALsdGEPhB](https://openreview.net/pdf?id=NALsdGEPhB)
