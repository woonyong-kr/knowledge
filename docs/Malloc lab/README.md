# Malloc lab

<!-- description:start -->
동적 메모리 할당자 구현. 할당 정책과 단편화 분석.
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->
- [implicit](./implicit/README.md) — Implicit Free List 기반 할당자.
- [explicit](./explicit/README.md) — Explicit Free List 기반 할당자.
- [seglist](./seglist/README.md) — Segregated Free List 기반 할당자.
- [buddy system](./buddy%20system/README.md) — Buddy System 할당자.
- [Fragmentation](./Fragmentation/README.md) — Internal·External 단편화의 원인과 완화 기법.
  - Internal Fragmentation
  - External Fragmentation
- [동적 메모리 할당](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/README.md) — 힙 영역에서 sbrk·malloc·free·realloc 로 이뤄지는 메모리 할당 흐름.
  - [힙](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/%ED%9E%99/README.md) — 프로세스 힙 영역의 구조·확장 방식.
  - [sbrk](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/sbrk/README.md) — sbrk 시스템콜과 힙 끝 포인터 이동.
  - [brk](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/brk/README.md) — brk 시스템콜 원리와 sbrk 와의 관계.
  - [malloc](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/malloc/README.md) — malloc 호출 흐름과 구현 전략.
  - [free](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/free/README.md) — free 호출 흐름과 메타데이터 복원.
  - [realloc](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/realloc/README.md) — realloc 의 제자리 확장·재할당 규칙.
  - [heap allocator 내부 구조](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/heap%20allocator%20%EB%82%B4%EB%B6%80%20%EA%B5%AC%EC%A1%B0/README.md) — 헤더·푸터·가용 리스트·정렬 정책 등 할당자 내부 자료구조.
  - [헤더 하위 3비트 트릭](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/%ED%97%A4%EB%8D%94%20%ED%95%98%EC%9C%84%203%EB%B9%84%ED%8A%B8%20%ED%8A%B8%EB%A6%AD/README.md) — 8바이트 정렬 전제로 하위 3비트를 메타로 쓰는 기법.
  - [split 과 coalesce](./%EB%8F%99%EC%A0%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC%20%ED%95%A0%EB%8B%B9/split%20%EA%B3%BC%20coalesce/README.md) — 블록 분할·인접 가용 블록 병합 정책.
- [할당 정책](./%ED%95%A0%EB%8B%B9%20%EC%A0%95%EC%B1%85/README.md) — 가용 블록 중 어떤 블록을 고를지 결정하는 탐색 전략.
  - first fit
  - next fit
  - best fit
- [Coalescing](./Coalescing/README.md) — 해제된 인접 가용 블록을 병합해 외부 단편화를 줄이는 기법.
  - 경계 태그
  - 즉시 병합
  - 지연 병합
- [성능 지표](./%EC%84%B1%EB%8A%A5%20%EC%A7%80%ED%91%9C/README.md) — 할당자 성능 평가 지표. Malloc lab 점수 산정에 사용.
  - 메모리 이용률 util
  - 처리량 thru
  - 테스트 스크립트
<!-- tree:end -->
