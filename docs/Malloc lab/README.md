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
  - 힙
  - sbrk
  - brk
  - malloc
  - free
  - realloc
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
<!-- tree:end -->
