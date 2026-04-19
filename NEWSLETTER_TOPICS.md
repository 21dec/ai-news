# Newsletter Topics Backlog

이 문서는 AI 뉴스레터 발행을 위한 글감(소재)을 관리하는 백로그입니다. 뉴스레터를 작성하면서 파생되는 새로운 아이디어나 후속 기술들은 [New Ideas / Spinoffs] 섹션에 지속적으로 추가됩니다.

## 📋 [Backlog] 작성 대기 중인 주제
* **RAG 파이프라인 파서 라우팅: Magika 기반 콘텐츠 타입 감지로 docx/pdf/script 분기** `[rag]` #rag #parser-routing #preprocessing
  > RAG 전처리 단계에서 업로드 파일을 확장자 대신 Magika의 콘텐츠 타입 + confidence 기반으로 파서(pypdf, python-docx, Unstructured, Tree-sitter 등)에 라우팅하는 실전 패턴을 다룹니다.
  > *(스핀오프 from: Magika: libmagic의 오탐을 걷어내는 1MB CNN 기반 파일 타입 검출기 | 추가: 2026-04-19)*
* **업로드 게이트 다층 방어: Magika + ClamAV + YARA 조합 설계** `[security]` #security #clamav #yara #defense-in-depth
  > 콘텐츠 타입 판정(Magika), 안티바이러스 스캐닝(ClamAV), 시그니처 기반 악성 패턴 매칭(YARA)을 단일 파이프라인에 배치하는 레이어링 전략과 각 단계의 임계값·타임아웃·폴백 규칙을 정리합니다.
  > *(스핀오프 from: Magika: libmagic의 오탐을 걷어내는 1MB CNN 기반 파일 타입 검출기 | 추가: 2026-04-19)*
* **libmagic vs Magika 정확도 실측: 사내 파일 코퍼스로 F1·레이턴시 벤치마크** `[evaluation]` #evaluation #benchmark #file-detection
  > 공개 데이터셋이 아닌 실제 사내 업로드 로그에서 추출한 혼합 포맷 코퍼스를 사용해 libmagic·Magika·확장자 기반 판정의 Top-1 정확도, F1, p95 레이턴시를 측정하는 방법론과 결과 해석을 다룹니다.
  > *(스핀오프 from: Magika: libmagic의 오탐을 걷어내는 1MB CNN 기반 파일 타입 검출기 | 추가: 2026-04-19)*
* **LangGraph 체크포인터 성능 튜닝: SqliteSaver vs AsyncPostgresSaver 실측** `[evaluation]` #langgraph #checkpoint #latency #benchmark
  > 고빈도 tool 루프에서 체크포인트 I/O가 레이턴시 병목이 되는 지점과 비동기 saver 전환 시 개선폭을 측정한다.
  > *(스핀오프 from: 단방향 체인을 넘어: LangGraph 1.1로 보는 순환 워크플로우와 상태 관리 실전 | 추가: 2026-04-19)*
* **LangGraph + Temporal: 언제 프레임워크 내장 durable execution만으로 충분한가** `[architecture]` #langgraph #temporal #workflow #durable-execution
  > LangGraph의 durable execution이 워크플로우 엔진을 완전히 대체할 수 있는 시나리오와 Temporal/Airflow를 겸용해야 하는 시나리오를 구분한다.
  > *(스핀오프 from: 단방향 체인을 넘어: LangGraph 1.1로 보는 순환 워크플로우와 상태 관리 실전 | 추가: 2026-04-19)*
* **StateSchema 마이그레이션 가이드: TypedDict에서 Zod/Pydantic으로** `[framework]` #langgraph #statescheme #zod #pydantic #migration
  > 2026년 1월 도입된 StateSchema로 기존 TypedDict 기반 상태를 옮기는 단계별 패턴과 런타임 검증 이점.
  > *(스핀오프 from: 단방향 체인을 넘어: LangGraph 1.1로 보는 순환 워크플로우와 상태 관리 실전 | 추가: 2026-04-19)*
* **vLLM + FP8 서빙: DeepGEMM 실제 통합 가이드** `[infra]` #vllm #fp8 #serving #integration
  > vLLM의 FP8 지원 현황과 DeepGEMM 커널을 custom backend로 연결하는 실전 방법
  > *(스핀오프 from: DeepGEMM: FP8 GEMM 커널 | 추가: 2026-04-19)*
* **GPTQ/AWQ vs FP8: 실측 벤치마크로 보는 양자화 선택 기준** `[evaluation]` #quantization #benchmark #gptq #awq
  > Post-training quantization 3가지 방식의 정확도·속도·메모리 트레이드오프를 동일 조건에서 비교
  > *(스핀오프 from: DeepGEMM: FP8 GEMM 커널 | 추가: 2026-04-19)*
* **초경량 In-process 벡터 DB (NanoVec) 활용 가이드** (초안 작성 완료)
* **로컬 LLM 서빙 비용 70% 절감:** vLLM과 PagedAttention을 활용한 인프라 아키텍처
* **RAG 파이프라인의 환각 수치화:** 오픈소스 평가 프레임워크 'Ragas' 도입기
* **멀티모달 데이터 전처리:** Vision-Language Model(VLM)을 활용한 복잡한 재무제표 PDF 파싱 파이프라인
* **자율형 코딩 에이전트(Agentic IDE):** Aider를 활용한 다중 파일 리팩토링 및 TDD 자동화

## ✍️ [In Progress] 작성 중
* (현재 작성 중인 글감이 이곳에 위치합니다)

## ✅ [Published] 발행 완료
* **Magika: libmagic의 오탐을 걷어내는 1MB CNN 기반 파일 타입 검출기** — `2026-04-19` [https://github.com/google/magika](https://github.com/google/magika) #content-detection #tooling #pipeline #classification
* **단방향 체인을 넘어: LangGraph 1.1로 보는 순환 워크플로우와 상태 관리 실전** — `2026-04-19` [https://github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) #agent #framework #langgraph #workflow #state
* **FlashAttention-3 vs DeepGEMM: H100 메모리 최적화, 두 갈래의 접근법** — `2026-04-19` [https://github.com/Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention) #attention #h100 #fp8 #hopper #gemm #architecture
* **DeepGEMM: DeepSeek이 공개한 FP8 GEMM 커널, GPU 비용의 판도를 바꾼다** — `2026-04-19` [https://github.com/deepseek-ai/DeepGEMM](https://github.com/deepseek-ai/DeepGEMM) #infra #fp8 #gemm #inference #deepseek
* (발행이 완료된 뉴스레터 목록과 발행일자를 기록합니다)

## 💡 [New Ideas / Spinoffs] 생성된 글로부터 포착된 신규 글감
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
* `[architecture]` **FlashAttention-3 vs DeepGEMM: H100 메모리 최적화 두 접근법 비교** ← DeepGEMM: FP8 GEMM 커널 작성 중 포착
  > DeepGEMM에서 wgmma/TMA 언급 → FlashAttention-3도 같은 H100 명령어 활용, 접근법 차이 탐색
* `[infra]` **vLLM + FP8 서빙: DeepGEMM 실제 통합 가이드** ← DeepGEMM: FP8 GEMM 커널 작성 중 포착
  > 실무 도입 섹션에서 vLLM 통합 복잡도를 언급했지만 구체적 방법은 다루지 않음
* `[evaluation]` **GPTQ/AWQ vs FP8: 실측 벤치마크로 보는 양자화 선택 기준** ← DeepGEMM: FP8 GEMM 커널 작성 중 포착
  > 정확도 검증 섹션에서 FP8 품질 주의를 언급 → 다른 양자화 방식과의 실측 비교 필요성 파생
*(뉴스레터를 작성하다가 파생된 추가적인 기술적 호기심이나 후속 주제를 이곳에 기록합니다)*
* *예시: 로컬 벡터 DB 글 작성 중 포착 -> "NanoVec 같은 로컬 DB와 클라우드 DB를 하이브리드로 구성하는 라우팅 전략"*
* *예시: LangGraph 글 작성 중 포착 -> "Agentic Workflow에서 무한 루프(Infinite Loop)에 빠지는 현상 방지를 위한 서킷 브레이커(Circuit Breaker) 패턴"*
