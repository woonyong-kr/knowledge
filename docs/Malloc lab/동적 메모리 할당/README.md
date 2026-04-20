# 동적 메모리 할당

<!-- description:start -->
힙 영역에서 sbrk·malloc·free·realloc 로 이뤄지는 메모리 할당 흐름.
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->
- [힙](./%ED%9E%99/README.md) — 프로세스 힙 영역의 구조·확장 방식.
- [sbrk](./sbrk/README.md) — sbrk 시스템콜과 힙 끝 포인터 이동.
- [brk](./brk/README.md) — brk 시스템콜 원리와 sbrk 와의 관계.
- [malloc](./malloc/README.md) — malloc 호출 흐름과 구현 전략.
- [free](./free/README.md) — free 호출 흐름과 메타데이터 복원.
- [realloc](./realloc/README.md) — realloc 의 제자리 확장·재할당 규칙.
- [heap allocator 내부 구조](./heap%20allocator%20%EB%82%B4%EB%B6%80%20%EA%B5%AC%EC%A1%B0/README.md) — 헤더·푸터·가용 리스트·정렬 정책 등 할당자 내부 자료구조.
- [헤더 하위 3비트 트릭](./%ED%97%A4%EB%8D%94%20%ED%95%98%EC%9C%84%203%EB%B9%84%ED%8A%B8%20%ED%8A%B8%EB%A6%AD/README.md) — 8바이트 정렬 전제로 하위 3비트를 메타로 쓰는 기법.
- [split 과 coalesce](./split%20%EA%B3%BC%20coalesce/README.md) — 블록 분할·인접 가용 블록 병합 정책.
<!-- tree:end -->

## 포스트

<!-- posts:start -->
(없음)
<!-- posts:end -->
