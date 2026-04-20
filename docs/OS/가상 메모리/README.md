# 가상 메모리

<!-- description:start -->
가상 주소 공간·프로세스 주소공간·execve·fork COW·mmap 4조합·task_struct·VMA.
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->
- 3대 문제 고립 정체성 용량
- 프로세스 주소 공간 레이아웃
- task_struct mm_struct VMA
- [execve와 ELF 로딩](./execve%EC%99%80%20ELF%20%EB%A1%9C%EB%94%A9/README.md) — execve 호출부터 ELF 로딩·프로세스 주소 공간 초기화까지의 흐름.
- [fork와 Copy on Write](./fork%EC%99%80%20Copy%20on%20Write/README.md) — fork 시 페이지 테이블 복제·쓰기 발생 시 COW 동작.
- [mmap 네 가지 조합](./mmap%20%EB%84%A4%20%EA%B0%80%EC%A7%80%20%EC%A1%B0%ED%95%A9/README.md) — private/shared × anonymous/file-backed 네 조합의 의미와 사용처.
- VMA vs 페이지 테이블
- Resident vs Not Resident
<!-- tree:end -->

## 포스트

<!-- posts:start -->
- [os-virtual-memory-process-address-space](./os-virtual-memory-process-address-space.md)
- [os-virtual-memory-task-struct-mm-struct-vma](./os-virtual-memory-task-struct-mm-struct-vma.md)
- [os-virtual-memory-three-problems](./os-virtual-memory-three-problems.md)
<!-- posts:end -->
