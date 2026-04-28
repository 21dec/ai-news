# Newsletter Topics Backlog

이 문서는 AI 뉴스레터 발행을 위한 글감(소재)을 관리하는 백로그입니다. 뉴스레터를 작성하면서 파생되는 새로운 아이디어나 후속 기술들은 [New Ideas / Spinoffs] 섹션에 지속적으로 추가됩니다.

## 📋 [Backlog] 작성 대기 중인 주제
* **합성 데이터의 품질은 어떻게 평가하나: 생성량이 아닌 전이 가능성 중심 벤치마크 설계** `[evaluation]` #SyntheticData #benchmarking #generalization
  > 합성 데이터는 그럴듯해 보이는 것만으로는 충분하지 않고, 실제 업무 분포에서 성능이 오르는지까지 검증해야 합니다. 이 주제는 생성 데이터가 진짜로 일반화에 기여하는지 판단하는 평가 지표와 실험 설계를 다루며, 데이터 증강이 오히려 성능을 망치는 상황을 줄이는 데 중요합니다.
  > *(스핀오프 from: 합성 데이터의 핵심은 생성량이 아니라 메커니즘 설계입니다 | 추가: 2026-04-20)*
* **Codex의 computer use는 얼마나 안전한가: 로컬 앱 조작 에이전트의 권한 격리·승인 플로우·감사 로그 설계** `[security]` #Codex #ComputerUse #Sandboxing
  > Codex가 IDE를 넘어 브라우저·터미널·로컬 앱까지 조작하기 시작하면 생산성보다 먼저 부딪히는 문제는 보안과 통제입니다. AI 엔지니어는 어떤 권한 모델, 사용자 승인 단계, 실행 샌드박스, 로그 체계를 갖춰야 실제 팀 환경에서 안심하고 배포할 수 있는지 궁금해할 가능성이 큽니다.
  > *(스핀오프 from: Codex, 코드 생성기를 넘어 개발 워크스테이션으로 확장 | 추가: 2026-04-20)*
* **LLM 내부 Attention Head 프루닝 실전: ProxySPEX로 MMLU 최적 서브셋 탐색** `[architecture]` #pruning #attention #optimization #spex
  > 본문에서 ProxySPEX 기반 프루닝이 성능을 향상시킬 수 있다고 언급했지만, 실제 모델별(Llama, Mistral 등) 프루닝 비율과 태스크별 성능 변화를 실측하는 가이드가 필요합니다.
  > *(스핀오프 from: SPEX: 수천 개 피처에서 LLM의 상호작용을 찾아내는 희소 복원 기반 해석 프레임워크 | 추가: 2026-04-19)*
* **도메인별 복잡도 보정: 합성 데이터의 난이도 분포가 다운스트림 성능에 미치는 비선형 효과** `[evaluation]` #synthetic-data #complexity #evaluation #domain-specific
  > 본문에서 수학은 높은 복잡도가 +10%를 가져오지만 법률에서는 오히려 하락한다고 언급했는데, 도메인별 최적 난이도 분포를 탐색하는 체계적 방법론이 필요합니다.
  > *(스핀오프 from: Simula: 합성 데이터 생성을 메커니즘 디자인으로 재구성한 Google의 프레임워크 | 추가: 2026-04-19)*
* **계층형 메모리 압축: L4 Session Archive의 요약 전략과 정보 손실 측정** `[architecture]` #memory #compression #architecture #summarization
  > 본문에서 L4 Session Archive가 과거 작업을 압축 저장한다고 언급했지만 어떤 요약 알고리즘을 쓰고, 정보 손실이 후속 작업 성공률에 미치는 영향은 다루지 않아 후속 글로 자연스럽게 이어집니다.
  > *(스핀오프 from: GenericAgent: 3,000줄 시드 코드에서 자라나는 자기 진화형 스킬 트리 | 추가: 2026-04-19)*
* **에이전트 스킬 트리의 이식성: 환경 변경 시 결정화된 스킬의 유효성 검증 프레임워크** `[evaluation]` #skill-tree #portability #evaluation #testing
  > 본문에서 각 인스턴스의 스킬 트리가 배포 환경에 따라 분화한다고 언급했는데, OS 또는 패키지 버전이 변경되었을 때 기존 스킬의 유효성을 자동 검증하고 재결정화하는 프레임워크 설계가 필요합니다.
  > *(스핀오프 from: GenericAgent: 3,000줄 시드 코드에서 자라나는 자기 진화형 스킬 트리 | 추가: 2026-04-19)*
* **handoff 도중의 스트리밍 응답 처리: 에이전트 전환 경계에서의 토큰 연속성** `[agent]` #agents-sdk #streaming #handoff
  > handoff 가 발생하는 순간 원래 에이전트의 스트림이 끊기고 새 에이전트의 스트림이 시작되는 구간에서 토큰 손실·중복·UI 깜박임을 막기 위한 버퍼링·시그널링 설계 패턴을 정리합니다.
  > *(스핀오프 from: Swarm을 넘어서: OpenAI Agents SDK의 handoff 중심 멀티에이전트 설계 | 추가: 2026-04-19)*
* **Magika ONNX Runtime 이식: 브라우저·엣지에서의 파일 타입 검출 지연 측정** `[tooling]` #magika #onnx #edge #wasm
  > Python 배포 환경에 묶여 있던 Magika 를 ONNX Runtime(Web·Mobile) 으로 이식해 업로드 게이트를 클라이언트 단에서 먼저 수행할 때의 p95 지연·메모리·정확도 회귀를 실측합니다.
  > *(스핀오프 from: Magika: libmagic의 오탐을 걷어내는 1MB CNN 기반 파일 타입 검출기 | 추가: 2026-04-19)*
* **LangGraph interrupt() 기반 Human-in-the-Loop: 승인 게이트와 에스컬레이션 설계** `[agent]` #langgraph #human-in-the-loop #interrupt #approval-gate
  > 1.1 에서 정식화된 `interrupt()` API 로 위험 툴 실행 직전 사용자 승인을 받는 게이트·타임아웃 시 자동 에스컬레이션·재개 시 상태 복원을 결합한 실전 패턴을 다룹니다.
  > *(스핀오프 from: 단방향 체인을 넘어: LangGraph 1.1로 보는 순환 워크플로우와 상태 관리 실전 | 추가: 2026-04-19)*
* **MoE 라우팅에서 FP8 GEMM 적용: expert 부하 불균형이 커널 효율에 미치는 영향** `[infra]` #moe #fp8 #gemm #load-balancing
  > 전체 토큰을 균등 분산한 dense GEMM 과 달리 MoE 는 expert 별 토큰 수가 편향되어 FP8 커널의 MMA·타일 사이즈가 낭비되는 구조를 분석하고, capacity factor·drop-token 비율별 실측 처리량을 정리합니다.
  > *(스핀오프 from: FlashAttention-3 vs DeepGEMM: H100 메모리 최적화, 두 갈래의 접근법 | 추가: 2026-04-19)*
* **DeepGEMM 기반 FP8 pre-training: 손실 발산 없이 안정화하는 동적 스케일링 전략** `[training]` #fp8 #pretraining #numerical-stability #scaling
  > 추론 영역에 머물던 FP8 GEMM 을 pre-training 루프에 투입할 때 발생하는 수치 발산을 per-tensor·per-block 동적 스케일링과 selective-precision 으로 억제하는 DeepSeek·NVIDIA 공개 레시피를 비교합니다.
  > *(스핀오프 from: DeepGEMM: DeepSeek이 공개한 FP8 GEMM 커널, GPU 비용의 판도를 바꾼다 | 추가: 2026-04-19)*
* **로컬 LLM 서빙 비용 70% 절감:** vLLM과 PagedAttention을 활용한 인프라 아키텍처
* **RAG 파이프라인의 환각 수치화:** 오픈소스 평가 프레임워크 'Ragas' 도입기
* **멀티모달 데이터 전처리:** Vision-Language Model(VLM)을 활용한 복잡한 재무제표 PDF 파싱 파이프라인
* **자율형 코딩 에이전트(Agentic IDE):** Aider를 활용한 다중 파일 리팩토링 및 TDD 자동화

## ✍️ [In Progress] 작성 중
* (현재 작성 중인 글감이 이곳에 위치합니다)

## ✅ [Published] 발행 완료
* **초 단위 AI 전력 추정, 스케줄러가 기다리지 않는 이유** — `2026-04-28` [https://news.mit.edu/2026/faster-way-to-estimate-ai-power-consumption-0427](https://news.mit.edu/2026/faster-way-to-estimate-ai-power-consumption-0427) #전력최적화 #데이터센터 #AI인프라 #스케줄링 #infra
* **LLM이 모르면 멈추게 하는 법, MIT의 신뢰도 캘리브레이션 접근** — `2026-04-27` [https://news.mit.edu/2026/teaching-ai-models-to-say-im-not-sure-0422](https://news.mit.edu/2026/teaching-ai-models-to-say-im-not-sure-0422) #LLM #AI Reliability #Calibration #Hallucination #evaluation
* **AI 제품 운영 데이터를 한 스택으로 묶는 방법, PostHog** — `2026-04-26` [https://github.com/PostHog/posthog](https://github.com/PostHog/posthog) #tooling #Feature Flags #AI Analytics #Observability #Product Analytics
* **합성 데이터의 핵심은 생성량이 아니라 메커니즘 설계입니다** — `2026-04-20` [https://research.google/blog/designing-synthetic-datasets-for-the-real-world-mechanism-design-and-reasoning-from-first-principles/](https://research.google/blog/designing-synthetic-datasets-for-the-real-world-mechanism-design-and-reasoning-from-first-principles/) #GoogleResearch #LLM #training #DataEngineering #SyntheticData
* **Codex, 코드 생성기를 넘어 개발 워크스테이션으로 확장** — `2026-04-20` [https://openai.com/index/codex-for-almost-everything](https://openai.com/index/codex-for-almost-everything) #AI에이전트 #Codex #DeveloperTools #tooling #OpenAI
* **SPEX: 수천 개 피처에서 LLM의 상호작용을 찾아내는 희소 복원 기반 해석 프레임워크** — `2026-04-19` [http://bair.berkeley.edu/blog/2026/03/13/spex/](http://bair.berkeley.edu/blog/2026/03/13/spex/) #evaluation #interpretability #interaction #spex
* **Simula: 합성 데이터 생성을 메커니즘 디자인으로 재구성한 Google의 프레임워크** — `2026-04-19` [https://research.google/blog/designing-synthetic-datasets-for-the-real-world-mechanism-design-and-reasoning-from-first-principles/](https://research.google/blog/designing-synthetic-datasets-for-the-real-world-mechanism-design-and-reasoning-from-first-principles/) #training #synthetic-data #mechanism-design #google
* **GenericAgent: 3,000줄 시드 코드에서 자라나는 자기 진화형 스킬 트리** — `2026-04-19` [https://github.com/lsdefine/GenericAgent](https://github.com/lsdefine/GenericAgent) #architecture #agent #memory #efficiency #skill-tree
* **Project Glasswing: Mythos Preview 가 드러낸 LLM 보안 감사의 임계점** — `2026-04-19` [https://www.anthropic.com/glasswing](https://www.anthropic.com/glasswing) #frontier-model #security #zero-day #glasswing
* **Swarm을 넘어서: OpenAI Agents SDK의 handoff 중심 멀티에이전트 설계** — `2026-04-19` [https://github.com/openai/openai-agents-python](https://github.com/openai/openai-agents-python) #agent #handoff #multi-agent #openai
* **Magika: libmagic의 오탐을 걷어내는 1MB CNN 기반 파일 타입 검출기** — `2026-04-19` [https://github.com/google/magika](https://github.com/google/magika) #content-detection #tooling #pipeline #classification
* **단방향 체인을 넘어: LangGraph 1.1로 보는 순환 워크플로우와 상태 관리 실전** — `2026-04-19` [https://github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) #agent #framework #langgraph #workflow #state
* **FlashAttention-3 vs DeepGEMM: H100 메모리 최적화, 두 갈래의 접근법** — `2026-04-19` [https://github.com/Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention) #attention #h100 #fp8 #hopper #gemm #architecture
* **DeepGEMM: DeepSeek이 공개한 FP8 GEMM 커널, GPU 비용의 판도를 바꾼다** — `2026-04-19` [https://github.com/deepseek-ai/DeepGEMM](https://github.com/deepseek-ai/DeepGEMM) #infra #fp8 #gemm #inference #deepseek
* (발행이 완료된 뉴스레터 목록과 발행일자를 기록합니다)

## 💡 [New Ideas / Spinoffs] 생성된 글로부터 포착된 신규 글감
* `[evaluation]` **합성 데이터의 품질은 어떻게 평가하나: 생성량이 아닌 전이 가능성 중심 벤치마크 설계** ← 합성 데이터의 핵심은 생성량이 아니라 메커니즘 설계입니다 작성 중 포착
  > 본문에서 합성 데이터의 기준이 '생성량'에서 '전이 가능성'으로 이동한다고 강조한 부분에서 자연스럽게 파생됩니다.
* `[security]` **Codex의 computer use는 얼마나 안전한가: 로컬 앱 조작 에이전트의 권한 격리·승인 플로우·감사 로그 설계** ← Codex, 코드 생성기를 넘어 개발 워크스테이션으로 확장 작성 중 포착
  > 원문이 코드 생성의 병목이 모델이 아니라 운영체제와 앱을 다루는 실행 계층이라고 짚었기 때문에, 그 실행 계층을 실제로 도입할 때의 핵심 후속 질문은 안전하게 어떻게 통제할 것인가입니다.
* `[architecture]` **LLM 내부 Attention Head 프루닝 실전: ProxySPEX로 MMLU 최적 서브셋 탐색** ← SPEX: 수천 개 피처에서 LLM의 상호작용을 찾아내는 희소 복원 기반 해석 프레임워크 작성 중 포착
  > 프루닝 적용의 구체적 실전 가이드가 본문에서 부재
* `[evaluation]` **도메인별 복잡도 보정: 합성 데이터의 난이도 분포가 다운스트림 성능에 미치는 비선형 효과** ← Simula: 합성 데이터 생성을 메커니즘 디자인으로 재구성한 Google의 프레임워크 작성 중 포착
  > 복잡도 조정 효과의 도메인 의존성이 실무적으로 중요하지만 본문에서 정밀하게 다루지 않음
* `[architecture]` **계층형 메모리 압축: L4 Session Archive의 요약 전략과 정보 손실 측정** ← GenericAgent: 3,000줄 시드 코드에서 자라나는 자기 진화형 스킬 트리 작성 중 포착
  > 본문의 5계층 메모리 아키텍처 설명에서 L4의 구체적 압축 메커니즘이 생략되어 있음
* `[evaluation]` **에이전트 스킬 트리의 이식성: 환경 변경 시 결정화된 스킬의 유효성 검증 프레임워크** ← GenericAgent: 3,000줄 시드 코드에서 자라나는 자기 진화형 스킬 트리 작성 중 포착
  > 환경 의존적 스킬 트리의 이식성 한계가 본문에서 도입 고려사항으로 언급됨
* `[tooling]` **Agents SDK 트레이싱을 OpenTelemetry로 내보내기: set_trace_processors 실전** ← Swarm을 넘어서: OpenAI Agents SDK의 handoff 중심 멀티에이전트 설계 작성 중 포착
  > 원글이 SDK의 기본 트레이싱을 언급했으나 외부 관측 스택 연동의 구체 절차와 태그 매핑은 다루지 않아 후속으로 자연스럽게 이어집니다.
* `[evaluation]` **멀티에이전트 회귀 테스트: handoff 라우팅 정확도를 측정하는 평가 셋 설계** ← Swarm을 넘어서: OpenAI Agents SDK의 handoff 중심 멀티에이전트 설계 작성 중 포착
  > 원글에서 '라우팅 정확도를 보장하려면 품이 더 든다'고만 언급했으므로 실제 평가 메트릭과 테스트 자동화를 다루는 별도 글로 분리하기 적합합니다.
* `[framework]` **Pydantic Guardrail 패턴: 입력 차단, 출력 검증, 툴 인자 스키마의 단일화** ← Swarm을 넘어서: OpenAI Agents SDK의 handoff 중심 멀티에이전트 설계 작성 중 포착
  > 원글에서 guardrail을 소개했지만 Pydantic 모델을 도구 스키마와 어떻게 공유하고 재사용하는지는 다루지 않아 실무 구현 패턴으로 확장 가능합니다.
* `[rag]` **RAG 파이프라인 파서 라우팅: Magika 기반 콘텐츠 타입 감지로 docx/pdf/script 분기** ← Magika: libmagic의 오탐을 걷어내는 1MB CNN 기반 파일 타입 검출기 작성 중 포착
  > 원글에서 Magika 의 활용 영역으로 RAG 전처리를 언급만 했을 뿐 구체적 라우팅 구현 패턴은 다루지 않아 후속 글로 자연스럽게 이어집니다.
* `[security]` **업로드 게이트 다층 방어: Magika + ClamAV + YARA 조합 설계** ← Magika: libmagic의 오탐을 걷어내는 1MB CNN 기반 파일 타입 검출기 작성 중 포착
  > 원글의 '헤더 위조 악성 페이로드' 언급에서 파생되는 후속 과제로, Magika 단독으로는 부족한 실제 악성 탐지 영역을 보강하는 설계 가이드가 필요합니다.
* `[evaluation]` **libmagic vs Magika 정확도 실측: 사내 파일 코퍼스로 F1·레이턴시 벤치마크** ← Magika: libmagic의 오탐을 걷어내는 1MB CNN 기반 파일 타입 검출기 작성 중 포착
  > 원글이 공개 벤치마크를 인용했지만 사내 분포에서의 실측은 다루지 않아, 내부 도입 결정에 필요한 검증 프레임이 후속 과제로 남았습니다.
* `[evaluation]` **LangGraph 체크포인터 성능 튜닝: SqliteSaver vs AsyncPostgresSaver 실측** ← 단방향 체인을 넘어: LangGraph 1.1로 보는 순환 워크플로우와 상태 관리 실전 작성 중 포착
  > 본문에서 체크포인터 I/O가 병목이 된다고 언급했지만 구체적 수치를 다루지 않음 — 실측 비교가 자연스러운 후속 주제.
* `[architecture]` **LangGraph + Temporal: 언제 프레임워크 내장 durable execution만으로 충분한가** ← 단방향 체인을 넘어: LangGraph 1.1로 보는 순환 워크플로우와 상태 관리 실전 작성 중 포착
  > 본문에서 '별도 워크플로우 엔진이 필요 없다'고 언급 — 어디까지 true한지 경계를 짚는 글이 필요함.
* `[framework]` **StateSchema 마이그레이션 가이드: TypedDict에서 Zod/Pydantic으로** ← 단방향 체인을 넘어: LangGraph 1.1로 보는 순환 워크플로우와 상태 관리 실전 작성 중 포착
  > 본문에서 StateSchema 도입을 요약만 했을 뿐 마이그레이션 실전을 다루지 않음.
* `[infra]` **vLLM + FP8 서빙: DeepGEMM 실제 통합 가이드** ← DeepGEMM: FP8 GEMM 커널 작성 중 포착
  > 실무 도입 섹션에서 vLLM 통합 복잡도를 언급했지만 구체적 방법은 다루지 않음
* `[evaluation]` **GPTQ/AWQ vs FP8: 실측 벤치마크로 보는 양자화 선택 기준** ← DeepGEMM: FP8 GEMM 커널 작성 중 포착
  > 정확도 검증 섹션에서 FP8 품질 주의를 언급 → 다른 양자화 방식과의 실측 비교 필요성 파생
*(뉴스레터를 작성하다가 파생된 추가적인 기술적 호기심이나 후속 주제를 이곳에 기록합니다)*
* *예시: 로컬 벡터 DB 글 작성 중 포착 -> "NanoVec 같은 로컬 DB와 클라우드 DB를 하이브리드로 구성하는 라우팅 전략"*
* *예시: LangGraph 글 작성 중 포착 -> "Agentic Workflow에서 무한 루프(Infinite Loop)에 빠지는 현상 방지를 위한 서킷 브레이커(Circuit Breaker) 패턴"*
