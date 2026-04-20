# OS

<!-- description:start -->
운영체제 핵심 개념. 프로세스·스레드, 스케줄링, 동기화, 가상 메모리, 캐시.
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->
- [OS의 정의](./OS%EC%9D%98%20%EC%A0%95%EC%9D%98/README.md) — 운영체제의 목적과 역할.
- [Process와 Thread](./Process%EC%99%80%20Thread/README.md) — 프로세스와 스레드의 구조·차이·비용.
  - 프로세스 vs 스레드
  - 스레드 풀 기본
  - OS 커널 스케줄러 관계
- [CPU Scheduling 알고리즘](./CPU%20Scheduling%20%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98/README.md) — FCFS·SJF·RR·Priority·MLFQS 스케줄링 정책.
- [Semaphore와 Mutex](./Semaphore%EC%99%80%20Mutex/README.md) — 두 대표 동기화 프리미티브의 의미와 차이.
- [Race Condition](./Race%20Condition/README.md) — 공유 자원 경쟁 상태의 원인과 예시.
- [Deadlock](./Deadlock/README.md) — 교착 상태의 조건·탐지·회피·예방.
- [Context Switching](./Context%20Switching/README.md) — 문맥 교환의 동작 원리와 비용.
- [System Call](./System%20Call/README.md) — 사용자 모드에서 커널 기능을 요청하는 메커니즘.
  - User vs Kernel mode
  - 커널 모드 진입 3가지 경로
  - syscall 경로
  - 커널 스레드
- [Kernel](./Kernel/README.md) — 커널의 역할과 구조·모놀리식 vs 마이크로.
- [Atomic Operation](./Atomic%20Operation/README.md) — 원자적 연산의 의미와 하드웨어 지원.
- [Interrupt](./Interrupt/README.md) — 인터럽트의 종류와 처리 흐름.
- [예외 제어 흐름](./%EC%98%88%EC%99%B8%20%EC%A0%9C%EC%96%B4%20%ED%9D%90%EB%A6%84/README.md) — CSAPP 8장. 예외·인터럽트·트랩·시그널·프로세스 제어의 통합 관점.
  - 예외의 4 가지 분류
  - 시그널 처리
  - setjmp longjmp
  - nonlocal jump
- [가상 메모리](./%EA%B0%80%EC%83%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC/README.md) — 가상 주소 공간·프로세스 주소공간·execve·fork COW·mmap 4조합·task_struct·VMA.
  - 3대 문제 고립 정체성 용량
  - 프로세스 주소 공간 레이아웃
  - task_struct mm_struct VMA
  - [execve와 ELF 로딩](./%EA%B0%80%EC%83%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC/execve%EC%99%80%20ELF%20%EB%A1%9C%EB%94%A9/README.md) — execve 호출부터 ELF 로딩·프로세스 주소 공간 초기화까지의 흐름.
  - [fork와 Copy on Write](./%EA%B0%80%EC%83%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC/fork%EC%99%80%20Copy%20on%20Write/README.md) — fork 시 페이지 테이블 복제·쓰기 발생 시 COW 동작.
  - [mmap 네 가지 조합](./%EA%B0%80%EC%83%81%20%EB%A9%94%EB%AA%A8%EB%A6%AC/mmap%20%EB%84%A4%20%EA%B0%80%EC%A7%80%20%EC%A1%B0%ED%95%A9/README.md) — private/shared × anonymous/file-backed 네 조합의 의미와 사용처.
  - VMA vs 페이지 테이블
  - Resident vs Not Resident
- [페이징 기법](./%ED%8E%98%EC%9D%B4%EC%A7%95%20%EA%B8%B0%EB%B2%95/README.md) — 페이지 단위 메모리 관리와 페이지 테이블.
  - [페이지 테이블 PTE](./%ED%8E%98%EC%9D%B4%EC%A7%95%20%EA%B8%B0%EB%B2%95/%ED%8E%98%EC%9D%B4%EC%A7%80%20%ED%85%8C%EC%9D%B4%EB%B8%94%20PTE/README.md) — 페이지 테이블 구조와 PTE 비트 의미.
  - [다단계 페이지 테이블](./%ED%8E%98%EC%9D%B4%EC%A7%95%20%EA%B8%B0%EB%B2%95/%EB%8B%A4%EB%8B%A8%EA%B3%84%20%ED%8E%98%EC%9D%B4%EC%A7%80%20%ED%85%8C%EC%9D%B4%EB%B8%94/README.md) — x86-64 4단계 페이징의 동작과 주소 분해.
  - [MMU](./%ED%8E%98%EC%9D%B4%EC%A7%95%20%EA%B8%B0%EB%B2%95/MMU/README.md) — MMU 의 주소 변환 단계와 캐시 상호작용.
  - CR3
  - VPN Offset 분해
  - 페이지 크기 4KB 근거
- [Cache](./Cache/README.md) — 캐시 계층 구조와 지역성 원리.
  - 메모리 계층
  - 캐시 라인과 지역성
  - 계층이 왜 필연인가
- [TLB](./TLB/README.md) — 주소 변환 캐시의 동작.
- [Page Fault](./Page%20Fault/README.md) — 페이지 부재의 원인과 처리 과정.
  - Page fault 분류
  - Demand paging
  - 메모리 보호 비트
- [linux redirection pipe](./linux%20redirection%20pipe/README.md) — 리눅스 셸의 리다이렉션과 파이프 동작.
- [DMA](./DMA/README.md) — Direct Memory Access. CPU 개입 없이 장치가 메모리에 직접 접근하는 기법.
- [demand-zero memory](./demand-zero%20memory/README.md) — 접근 시점에 0 으로 초기화된 페이지를 지연 할당하는 메모리 관리 기법.
<!-- tree:end -->
