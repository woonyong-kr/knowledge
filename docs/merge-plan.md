# Krafton-Jungle 병합 계획서 (재검토본)

> 이 문서는 병합 작업 승인 전용 계획서이다. 승인 후 tree.yaml 업데이트·파일 복사·커밋이 이 문서 기준으로 진행된다.
> 원본 위치: `_krafton/` (gitignore 처리됨, 공개 저장소에는 포함되지 않음).
> 검토 기준: `docs/CONTRIBUTING.md` 5·6·6.1·6.2 (파일·프런트매터·AI 흔적·이모지 금지) 준수.

## 1. 전체 점검 결과

- 검토 파일 수: 189 (venv·node_modules·dist·archive·webproxy-lab 실습 코드 제외)
- 실제 학습 콘텐츠: 약 150
- 직접 채택 (편집 최소, 프런트매터만 추가): 약 82
- 재작성·병합 필요 (제목 정리·헤더 교체·주차 메타 제거): 약 18
- 스킵 대상 (운영 메타·중복 legacy·1KB 미만·비어있음): 약 50

## 2. 중복 제거를 위한 tree.yaml 재정렬 원칙

1. **한 주제는 하나의 L1(또는 L2 이하) 에만 존재**한다. 포스트 간 참조는 본문 링크로만 한다.
2. L1 이름은 "책/주차"가 아닌 **학습 키워드**로 짓는다.
3. 각 L0 카테고리는 **엄격한 경계**를 가지며, 인접 카테고리와의 경계는 아래 매트릭스로 고정한다.
4. 한 L1 에 포스트가 3편 이상 누적되거나 단일 원본이 여러 하위 주제를 커버하면 해당 하위 주제를 **L2 폴더로 승격**한다 (CONTRIBUTING.md 1.2 절). 본 계획서 3.8 절 에 승격 대상 L2 목록을 둔다. L2 아래로도 필요 시 L10 까지 재귀 승격할 수 있다.
5. **알고리즘 문제 풀이는 지식 트리에 올리지 않는다.** 개념·자료구조 설명만 수용한다 (3.10 절).
6. **외부 원본(PDF, 강의 슬라이드 등) 도 키워드 소스로 인정**한다. 3.11 절 에 첨부 PDF 에서 도출된 키워드 제안이 있다.

### 2.1 카테고리 경계 매트릭스 (중복 방지)

| 주제 | 어디에 두는가 | 어디에 두지 않는가 |
|---|---|---|
| 메모리 계층·캐시 라인·지역성 | OS / Cache | CS 기초 X, Malloc lab X |
| 가상 주소 공간·VMA·COW·mmap·fork·execve | OS / 가상 메모리 | Malloc lab X, CS 기초 X |
| 페이지 테이블·PTE·다단계·MMU | OS / 페이징 기법 | 가상 메모리 X |
| TLB | OS / TLB | 페이징 기법 X |
| Page fault·Demand paging | OS / Page Fault | 가상 메모리 X |
| User/Kernel mode·System call | OS / System Call | Pintos X |
| brk·sbrk·heap 확장·allocator 내부 | Malloc lab / 동적 메모리 할당 | OS X |
| implicit·explicit·seglist·buddy | Malloc lab / (해당 L1) | — |
| 내/외 단편화·coalesce·split | Malloc lab / Fragmentation 또는 Coalescing | — |
| 메모리 버그·UB·포인터 메타데이터 부재 | CS 기초 / C에서 Pointer 및 배열 | OS X |
| GC·자동 수집 | CS 기초 / Garbage Collect | — |
| DB 페이지=OS 페이지=B+ 노드 공통 결정 | DB / 페이지 스토리지 | OS X, B+Tree X |
| 슬롯 페이지 레이아웃·페이지 타입 태그·memcpy 직렬화 | DB / 페이지 스토리지 | SQL 엔진 X |
| B+ Tree 삽입·분할·페이지 경계 split | DB / B Tree B+ Tree | 페이지 스토리지 X |
| 프레임 캐시·LRU·pin count·dirty bit | DB / SQL 엔진 | OS Cache X (OS Cache 는 하드웨어 캐시 계층) |
| pread·pwrite·O_DIRECT | DB / SQL 엔진 | OS X |
| SQL 파서·쿼리 플랜·실행기 | DB / SQL 엔진 | — |
| RESP·명령 디스패처·KV·Skip List·AOF·RDB | DB / Redis | — |
| Ethernet·Bridge·Router·LAN·WAN | 네트워크 / 네트워크 하드웨어 | OSI X |
| IP 주소 체계·byte order·DNS | 네트워크 / IP와 DNS | OSI X |
| socket·bind·listen·accept·connect·close | 네트워크 / 소켓 시스템콜 | OS System Call X |
| struct socket·sk_buff·sockfs·fd→socket 체인 | 네트워크 / 소켓 내부 구조 | OS X |
| I/O Bridge·DMA·PCIe·NIC ring | 네트워크 / I/O Bridge와 NIC | OS X |
| TCP/UDP·handshake·CLOSE_WAIT | 네트워크 / 전송 계층 TCP UDP | — |
| HTTP 메시지·METHOD·1.0/1.1·FTP·MIME | 네트워크 / HTTP 프로토콜 | — |
| Tiny 서버·Rio·parse_uri·serve_static·serve_dynamic | 네트워크 / Tiny 웹서버 | 웹서버 L1(개념) X |
| CGI·fork+execve·dup2·환경변수 인자 | 네트워크 / CGI 동적 처리 | Tiny 웹서버 X |
| Forward/Reverse Proxy·순차·동시·캐싱 | 네트워크 / Proxy 서버 | Tiny 웹서버 X |
| Thread Pool·async I/O·epoll·동시 서버 | 네트워크 / Concurrent Server | OS X |
| race condition 네트워크 서버 락 설계 | 네트워크 / 서버 동시성과 락 | OS Race Condition X (OS 쪽은 일반 개념) |
| Virtual DOM·Diff·Patch·Fiber·Hooks | 프로젝트 공통 지식 / React | — |

## 3. tree.yaml 최종안 (현재 vs 제안)

> diff 표기. 굵은 글씨 없이 ‘+ 추가 / − 삭제 / ~ 조정’만 표기.

### 3.1 CS 기초

```
~ name: C에서 Pointer 및 배열
    description: C 포인터의 의미·배열 관계·포인터 연산·메타데이터 부재로 생기는 메모리 버그.
+   sub:
+     - 포인터 기본
+     - 배열과 포인터
+     - 포인터 연산
+     - 참조형 동작 예제
+     - 메모리 버그 근본 원인
+     - Undefined Behavior
```
다른 L1 변경 없음.

### 3.2 Algorithm 및 Data Structures

```
+ - name: 자료구조 개요
+     description: 자료구조 분류·선택 기준과 시간·공간 복잡도 시각화.
+     sub:
+       - 순서가 중요한 문제
+       - 관계가 중요한 문제
+       - 연결이 중요한 문제
+       - 속도가 중요한 문제
```
문제풀이 인덱스(problems set)는 이 L1 하위 포스트로 수용.

### 3.3 Malloc lab

```
~ name: 동적 메모리 할당
+   sub:
+     - 힙
+     - sbrk
+     - brk
+     - malloc
+     - free
+     - realloc
+     - heap allocator 내부 구조
+     - 헤더 하위 3비트 트릭
+     - split 과 coalesce

~ name: 성능 지표
+   sub:
+     - 메모리 이용률 util
+     - 처리량 thru
+     - 테스트 스크립트
```

### 3.4 네트워크

현재 L1 유지하되 범위 재정의, 7개 L1 추가.

```
~ name: BSD 소켓              → 이름 유지, 범위 = 시스템콜 함수 + addrinfo + 호출 순서
~ name: 프록시 서버            → 이름 유지, 범위 = 순차·동시·캐싱 proxy 구현
~ name: TCP IP UDP HTTP file descriptor DNS → 이 L1은 broad하므로 4개로 분할
− name: TCP IP UDP HTTP file descriptor DNS
+ name: IP와 DNS
+     description: IP 주소 체계·byte order·DNS·도메인 등록·Cloudflare 경로.
+     sub:
+       - IPv4 32비트
+       - IPv6
+       - host·network byte order
+       - DNS 조회 원리
+       - 도메인 등록
+       - Cloudflare DNS/Proxy
+ name: 전송 계층 TCP UDP
+     description: TCP·UDP 차이·소켓 시스템콜 매핑·3way·4way·CLOSE_WAIT.
+     sub:
+       - TCP 3-way handshake
+       - 4-way 종료
+       - TIME_WAIT
+       - CLOSE_WAIT
+       - 소켓 버퍼
+       - tcp_sock 구조
+ name: HTTP 프로토콜
+     description: HTTP 메시지·METHOD·1.0/1.1·FTP·MIME·Telnet.
+     sub:
+       - HTTP 요청 응답
+       - HTTP METHOD
+       - HTTP 1.0 1.1 차이
+       - MIME type
+       - FTP 비교
+       - Telnet
+ name: 네트워크 하드웨어
+     description: Ethernet·Bridge·Router·LAN·WAN·NIC 의 역할과 차이.
+     sub:
+       - Ethernet
+       - Bridge·Switch
+       - Router
+       - LAN WAN
+       - NIC MAC
+ name: 소켓 내부 구조
+     description: struct socket·sk_buff·sockfs·fd→socket 포인터 체인·sk_receive_queue.
+     sub:
+       - fd to file to socket 체인
+       - struct socket vs struct sock
+       - sk_buff
+       - sockfs
+       - 소켓 버퍼 큐
+ name: I/O Bridge와 NIC
+     description: CPU·DRAM·NIC 경로·DMA·PCIe·TLP·MSI-X·NAPI.
+     sub:
+       - I/O Bridge IMC PCH
+       - DMA API
+       - PCIe TLP
+       - MSI-X
+       - NAPI
+       - NIC ring buffer
+ name: Tiny 웹서버
+     description: CSAPP Tiny 서버 함수 체인·Rio·parse_uri·serve_static·serve_dynamic.
+     sub:
+       - Tiny main 루프
+       - Rio 버퍼 I/O
+       - parse_uri
+       - serve_static
+       - serve_dynamic
+       - clienterror
+ name: CGI 동적 처리
+     description: CGI·fork+execve·dup2·환경변수·QUERY_STRING.
+     sub:
+       - CGI 개념
+       - fork execve 체인
+       - dup2로 표준출력 연결
+       - QUERY_STRING·환경변수
+ name: Concurrent Server
+     description: Iterative·Thread pool·async I/O·epoll·blocking vs non-blocking.
+     sub:
+       - Iterative server
+       - Thread pool
+       - async I/O
+       - epoll
+       - non-blocking I/O
+ name: 서버 동시성과 락
+     description: 네트워크 서버에서의 mutex·condvar·thread-safe 디자인.
+     sub:
+       - race condition in server
+       - mutex condvar
+       - thread-safe 카운터
+       - per-connection 상태
+       - thread pool 공유 자원

~ name: 웹서버                 → 기존 L1 유지하되 범위 = 웹서버 개념 일반 (tiny L1과 경계: 구현 X, 개념만)
~ name: 웹 컨텐츠              → 유지, MIME/static/dynamic 정책
~ name: HTTP 메시지 구조        → 유지, HTTP 메시지 라인·헤더·상태코드 세부
~ name: TCP IP 계층 모델        → 유지 (OSI 와 구분)
~ name: 클라이언트 서버 모델     → 유지
~ name: REST API               → 유지
~ name: HTTP METHOD            → 삭제, HTTP 프로토콜 L1로 흡수
~ name: OSI 7계층              → 유지
~ name: CDN                    → 유지
```

### 3.5 OS

```
~ name: 가상 메모리
    description: 가상 주소 공간·프로세스 주소공간·execve·fork COW·mmap 4조합·task_struct·VMA.
+   sub:
+     - 3대 문제 (고립 정체성 용량)
+     - 프로세스 주소 공간 레이아웃
+     - task_struct mm_struct VMA
+     - execve와 ELF 로딩
+     - fork와 Copy on Write
+     - mmap 네 가지 조합
+     - VMA vs 페이지 테이블
+     - Resident vs Not Resident

~ name: 페이징 기법
+   sub:
+     - 페이지 테이블 PTE
+     - 다단계 페이지 테이블
+     - MMU
+     - CR3
+     - VPN Offset 분해
+     - 페이지 크기 4KB 근거

~ name: Page Fault
+   sub:
+     - Page fault 분류
+     - Demand paging
+     - 메모리 보호 비트

~ name: Cache
+   sub:
+     - 메모리 계층
+     - 캐시 라인과 지역성
+     - 계층이 왜 필연인가

~ name: System Call
+   sub:
+     - User vs Kernel mode
+     - 커널 모드 진입 3가지 경로
+     - syscall 경로
+     - 커널 스레드

~ name: Process와 Thread
+   sub:
+     - 프로세스 vs 스레드
+     - 스레드 풀 기본
+     - OS 커널 스케줄러 관계
```

### 3.6 DB

```
~ name: B Tree B+ Tree
+   sub:
+     - B+ Tree 노드 구조
+     - 리프 내부 노드 분할
+     - 페이지 경계 Split
+     - 인덱스 탐색 흐름

+ - name: 페이지 스토리지
+     description: 디스크 기반 저장의 페이지 단위 레이아웃·타입 태그·슬롯·내부 단편화·memcpy 직렬화.
+     sub:
+       - 4KB 페이지 결정 근거
+       - 페이지 타입 태그 polymorphism
+       - 슬롯 페이지 레이아웃
+       - 내부 단편화 측정
+       - memcpy 기반 직렬화
+       - 헤더 힙 루트 리프 페이지

+ - name: SQL 엔진
+     description: 디스크 기반 미니 SQL 엔진의 전체 구조·프레임 캐시·B+Tree SQL 계획·파서.
+     sub:
+       - 프레임 캐시 LRU
+       - pread pwrite
+       - 이중 캐시 의심
+       - B+Tree SQL 계획
+       - SQL 파서
+       - 쿼리 플랜
+       - 성능 테스트 INDEX vs SCAN

+ - name: Redis
+     description: 인메모리 KV 스토어 Redis 의 프로토콜·명령 디스패처·자료구조·TTL·영속성·eviction.
+     sub:
+       - RESP 프로토콜
+       - 명령 디스패처
+       - String Hash List Set Sorted Set
+       - MurmurHash3
+       - Chained Hash Table
+       - Open Address Hash Table
+       - Skip List
+       - TTL lazy·active
+       - AOF·RDB 영속성
+       - maxmemory·eviction
+       - 느린 클라이언트 보호
```

### 3.7 프로젝트 공통 지식

```
+ - name: React
+     description: 선언적 UI 런타임 직접 구현으로 배우는 React 코어 개념.
+     sub:
+       - Virtual DOM
+       - Diff Patch
+       - Fiber 아키텍처
+       - Reconciliation
+       - Hooks
+       - 이벤트 위임
+       - 스케줄링과 우선순위
+       - createElement JSX
+       - demo SPA 설계 사례
```

### 3.8 L2 폴더 승격 대상 (신설)

`tree.yaml` 의 `sub` 항목을 문자열에서 객체(`{name, description, slug?}`) 로 승격할 후보. 단일 원본이 복수 하위 주제를 다루는 경우와, 향후 포스트 누적이 예상되는 경우를 묶었다. 승인되는 항목만 객체로 바꾸고 폴더를 생성한다.

| L0 / L1 | L2 (폴더 승격 후보) | 분할 원본 후보 | 비고 |
|---|---|---|---|
| OS / 가상 메모리 | mmap·munmap, fork·COW, execve 로드, 스왑 영역, brk·sbrk 경계 | W08 woonyong-kr 시리즈 (q01~q20 중 가상메모리 묶음), csapp-9 노트 | 단일 원본 분할이 가장 시급한 영역 |
| OS / 페이징 기법 | 페이지 테이블 구조, 다단계 페이징, MMU 동작, PTE 비트 의미 | W07-SQL/csapp-ch9-virtual-memory, W08/csapp-11 일부 | |
| OS / Cache | 캐시 라인·세트, 캐시 일관성, 지역성 분석 | W07-SQL/blog/concepts/01-memory-hierarchy, woonyong-kr q03 | |
| OS / System Call | 호출 진입(트랩), syscall 번호·테이블, errno 규약 | W08 woonyong-kr q04, q07 | |
| OS / Page Fault | minor·major fault, demand paging, fault 처리 흐름 | W07-SQL/csapp-ch9, W08 woonyong-kr q11 | |
| OS / Process와 Thread | 프로세스 생성·종료, 스케줄러 큐, 스레드 모델 | W08 woonyong-kr q15 등 | |
| Malloc lab / 동적 메모리 할당 | implicit list, explicit list, segregated list, buddy, coalesce, split, header·footer 메타, 정렬 정책, 단편화 측정 | W07-malloc-lab 전체, presenter-woonyong-allocator-and-memory-bugs | 9 sub 모두 폴더화 검토 |
| DB / 페이지 스토리지 | 슬롯 페이지, 페이지 헤더 포맷, 직렬화·역직렬화, 페이지 캐시 | W07-SQL/blog/applications, W08 csapp-11 | |
| DB / B Tree B+ Tree | 노드 구조, 삽입·분할, 탐색·범위 질의, 동시성 | W08/team/woonyong-kr B+Tree 시리즈 | |
| DB / SQL 엔진 | 파서·플래너, 실행기, 버퍼 풀·LRU 프레임 캐시, pread/pwrite/O_DIRECT | sql-feature-scope-roadmap (48KB) 분할 | 가장 큰 단일 원본 |
| DB / Redis | RESP 프로토콜, 명령 디스패처·dict, AOF·RDB 영속화, 자료구조(Skip List 등) | W03-redis README + 발표자료/cli 시나리오 | README 25KB 분할 |
| 네트워크 / 소켓 내부 구조 | 파일 디스크립터 생명주기·dispatch, struct socket·sk_buff, sockfs 와 fd→socket 체인 | q05-socket-principle, q20-fd-lifecycle-and-dispatch (42KB) | q20 분할 필수 |
| 네트워크 / Tiny 웹서버 | Rio 버퍼, parse_uri, serve_static, serve_dynamic | webproxy-lab 노트, W08 questions | |
| 네트워크 / Concurrent Server | Thread Pool, async I/O·epoll, 비교 | csapp-12 시리즈 | |
| 프로젝트 공통 지식 / React | Virtual DOM·Diff, Fiber·Reconciler, Hooks 모델 | W04-react·W05-react README | |

각 표 행에 대해 "Y(승격) / N(문자열 유지) / 일부(승격할 L2 만 별도 표시)" 로 회신해 주시면 4 절 표의 목적지·파일명·subkeyword 가 그에 맞춰 업데이트됩니다.

### 3.9 변경 없는 카테고리

- AI (신경망·LLM·AI 응용기술): 이번 범위에 해당 문서 없음.
- Pintos: 이번 범위에 해당 문서 없음.

### 3.10 알고리즘 문제 풀이 배제 정책

`Algorithm 및 Data Structures` 카테고리는 **개념 문서만** 수용한다. 직접적인 알고리즘 문제 풀이는 지식 트리에 올리지 않는다.

- 수용 대상: 자료구조 개요, 알고리즘 개념 설명, 복잡도 분석, 구현 스케치, 함정 모음, 언어 무관한 사고 흐름.
- 배제 대상: 특정 문제(백준·프로그래머스·LeetCode 등) 번호로 귀결되는 풀이, "문제 풀이 모음" 류 인덱스, 문제 지문 요약, 코드 덤프.
- 경계가 모호한 경우 기본값은 배제(SKIP). 승격 조건은 "해당 문제가 특정 개념의 **대표 예시** 로 쓰이는 경우" 에 한하며, 이때도 포스트 본문은 개념 설명으로 쓰고 문제는 보조 예시로만 등장시킨다.
- 복사·이관 워크플로(7 절) 에서 알고리즘 문제 풀이 파일은 `tech-blog-writing` 스킬에도 태우지 않는다. `_krafton/` 에 그대로 두거나 로컬 별도 디렉터리로 옮긴다.

### 3.11 첨부 PDF 기반 키워드 추가안

첨부로 제공된 3 개 PDF 의 목차·본문을 훑어 기존 `tree.yaml` 에 비는 키워드를 다음과 같이 제안한다. 각 항목은 3.1~3.7 과 동일한 `+ / − / ~` 표기를 쓴다. 승인 여부는 8 절 체크리스트에서 항목별로 회신해 주시면 된다.

#### 3.11.1 출처: `CSApp 공부법.pdf`

CSAPP 교재 12 장 챕터 구조를 키워드 보강 기준으로 사용한다. 기존 트리에 이미 반영된 챕터(가상 메모리·캐시·네트워크 프로그래밍 등) 는 재등장시키지 않고, 빠진 챕터만 L1 후보로 올린다.

```
~ L0: CS 기초
+ - name: 어셈블리 언어 기초
+     description: CSAPP 3장. x86-64 명령어·레지스터·호출 규약·스택 프레임.
+     sub:
+       - x86-64 레지스터
+       - 호출 규약과 스택 프레임
+       - 조건 분기와 점프
+       - 배열·구조체 어셈블리
+       - 포인터 연산과 주소 계산

+ - name: 프로그램 성능 최적화
+     description: CSAPP 5장. 컴파일러 최적화 한계·캐시 친화적 코드·프로파일링.
+     sub:
+       - 최적화 방해 요인
+       - 루프 최적화
+       - 캐시 친화적 코드
+       - 프로파일링 기법

+ - name: 링커와 로더
+     description: CSAPP 7장. 정적·동적 링킹·심볼 테이블·재배치·공유 라이브러리.
+     sub:
+       - 심볼 테이블
+       - 재배치 엔트리
+       - 정적 링킹
+       - 동적 링킹과 PIC
+       - 공유 라이브러리 로딩

~ L0: OS
+ - name: 예외 제어 흐름
+     description: CSAPP 8장. 예외·인터럽트·트랩·시그널·프로세스 제어의 통합 관점.
+     sub:
+       - 예외의 4 가지 분류
+       - 시그널 처리
+       - setjmp longjmp
+       - nonlocal jump
```

- 기존 `OS / Interrupt`, `OS / System Call` 와의 중복은 경계 매트릭스(2.1 절) 에 "예외 통합 관점은 예외 제어 흐름 L1, 하드웨어 인터럽트는 Interrupt L1, 시스템콜 진입은 System Call L1" 으로 분리하고 본 L1 이 승인되면 매트릭스에 행을 추가한다.

#### 3.11.2 출처: `PINTOS_전_C_기초_특강_발표자료 (1).pdf`

기존 `CS 기초 / C 언어 기초` L1 의 `sub` 를 발표자료 목차에 맞춰 확장한다.

```
~ name: C 언어 기초
    description: C 언어의 타입·포인터 감각·메모리 모델·표준 함수의 함정을 정리한 기초 묶음.
+   sub:
+     - 기본 자료형과 sizeof
+     - 포인터 감각 잡기
+     - 배열과 포인터의 실제 차이
+     - 스택과 힙의 경계
+     - struct 와 패딩
+     - typedef 의 쓰임새
+     - static 과 extern
+     - 표준 함수의 함정 Traps and Pitfalls
+     - 빌드 과정 전처리기 컴파일 링킹
```

- 기존 L1 내용을 덮어쓰지 않고 `sub` 만 확장한다. 일부 항목(스택과 힙의 경계) 은 기존 `CS 기초 / Stack과 Heap 메모리 구조` L1 과 겹치므로, 본 항목은 문자열 L2 로만 두고 폴더 승격 시 기존 L1 쪽으로 링크한다.

#### 3.11.3 출처: `Web to MSA.pdf`

```
~ L0: 네트워크
~ name: HTTP 프로토콜
+   sub:
+     - HTTP 1.0
+     - HTTP 1.1
+     - HTTP 2.0
+     - HTTP 3 QUIC
+     - Keep-Alive 와 파이프라이닝
+     - Server Push

+ - name: 동적 처리 모델 진화
+     description: CGI → FastCGI → 앱 서버 통합까지의 서버 측 동적 처리 방식 변천.
+     sub:
+       - CGI
+       - FastCGI
+       - 임베디드 스크립트 (mod_php 등)
+       - 3 Tier 아키텍처
+       - 리버스 프록시 + 앱 서버 조합

+ - name: 서버 아키텍처 패턴
+     description: 서비스 경계를 나누는 대표 패턴.
+     sub:
+       - Reverse Proxy
+       - Load Balancer
+       - API Gateway
+       - Service Discovery
+       - Backend for Frontend

~ name: REST API
+   sub:
+     - RESTful 원칙
+     - 리소스 모델링
+     - 상태 코드 설계
+     - HATEOAS
+     - RESTful vs RPC

~ L0: 프로젝트 공통 지식
+ - name: 아키텍처 패턴
+     description: Monolithic 과 Microservice 를 중심으로 한 서비스 분할·배포 패턴.
+     sub:
+       - Monolithic
+       - Modular Monolith
+       - Microservice 분할 기준
+       - 배포 경계와 DB 공유 정책
+       - 서비스 간 통신 패턴
+       - 관측성 로깅 추적
```

- 경계 매트릭스에 "HTTP 버전별 차이 → 네트워크/HTTP 프로토콜", "CGI·FastCGI → 네트워크/동적 처리 모델 진화", "Reverse Proxy·API Gateway·Load Balancer → 네트워크/서버 아키텍처 패턴", "Monolithic vs MSA → 프로젝트 공통 지식/아키텍처 패턴" 행을 신규로 추가한다.
- 기존 `네트워크 / CGI 동적 처리` L1 (3.4 절 에서 추가 제안된 L1) 과 본 `동적 처리 모델 진화` 사이의 중복은 피한다. 본 L1 이 승인되면 3.4 절 의 `CGI 동적 처리` L1 은 `동적 처리 모델 진화` 아래 L2 폴더로 흡수한다.

## 4. 파일별 배치·품질 판정표

총 189 파일. 아래 표기 규칙:
- **KEEP**: 원문 그대로 복사 + 프런트매터만 추가 (그래도 `tech-blog-writing` 스킬의 금지 패턴 체크리스트는 통과해야 함)
- **EDIT**: 제목·헤더·프로젝트 메타 라인 소폭 정리 후 복사. 톤만 스킬 규약에 맞춤.
- **REWRITE**: 재구성 필요 (주차 표기 제거·키워드 기준 재배열 등). `tech-blog-writing` 스킬 10단계에 맞춰 새로 씀.
- **SPLIT→X,Y**: 한 원본을 두 개 이상의 포스트로 분할. 각 조각이 향할 (L1, L2) 를 표기. 3.8 절 의 L2 승격이 전제.
- **MERGE→X**: 다른 파일과 병합, 대상 지정
- **SKIP**: 개인 운영·중복 legacy·incomplete·dev 환경 가이드

목적지 표기는 다음 형태를 따른다.
- `<L0>/<L1>` — L1 직속 포스트 (subkeyword 없음)
- `<L0>/<L1>/<L2>` — L2 폴더 안 포스트 (frontmatter `subkeyword: <L2>`)

본 표의 분할 매핑(SPLIT) 은 3.8 절 L2 승격 대상 응답 결과에 따라 마지막에 일괄 갱신한다.

> **주의 (2026-04-20 확정):** 본 표의 파일명과 목적지는 **L1 배정까지** 를 신뢰 대상으로 한다. 8 절의 L2 승격 Y 응답이 반영된 L1 (Malloc lab/동적 메모리 할당, OS/가상 메모리, OS/페이징 기법, DB/B Tree B+ Tree, DB/페이지 스토리지, DB/SQL 엔진, DB/Redis, 네트워크/소켓 내부 구조, 네트워크/Tiny 웹서버, 네트워크/동적 처리 모델 진화, 프로젝트 공통 지식/React) 에 배정된 포스트는 **실제 L2 폴더와 최종 파일명을 `tech-blog-writing` 스킬 호출 시점에 결정**한다. 파일명 prefix 는 `tree.yaml` 의 L2 `slug` 필드를 그대로 쓴다.

### 4.1 W00 / W01

| 파일 | 용량 | 판정 | 목적지 |
|---|---|---|---|
| SW_AI-W00/.../README.md | 19B | SKIP | 빈 README |
| SW_AI-W01/venv/**/LICENSE.md, ICON_LICENSE.md | - | SKIP | vendor license |

### 4.2 W02 계열

| 파일 | 용량 | 판정 | 목적지 |
|---|---|---|---|
| COMMON/SW-AI-ISSUE-TEMPLATE/README.md | 5.1KB | SKIP | GitHub Issue 템플릿 생성 가이드 (프로젝트 내부 툴) |
| SW-AI-W02-05/README.md | 2.6KB | SKIP | 팀 리포지토리 템플릿 |
| SW-AI-W02-05/problems set.md | 8.5KB | EDIT | Algorithm/자료구조 개요 → `algo-problems-set-overview.md` (이모지·주차 표기 제거) |
| SW-AI-W02-05/week3/data-structure/data-structure-basic.md | 9.9KB | EDIT | Algorithm/자료구조 개요 → `algo-data-structures-overview.md` |
| SW-AI-W02-05/week5/docs/{ai-principles,checklist,goal,team-collaboration}.md | 1~3KB | SKIP | 주차 운영 문서 |
| SW_AI-W02-workshop-openai/README.md | 8.7KB | SKIP | Clean Email 프로젝트 소개 (학습 키워드 아님) |
| SW_AI-W02-workshop-openai/.pytest_cache/README.md | 302B | SKIP | pytest 생성 파일 |
| SW_AI-W02-05/week3/data-structure/data-structure-basic.md | | 위 EDIT 로 통합 | |

### 4.3 W06 data_structures_docker

| 파일 | 용량 | 판정 | 목적지 |
|---|---|---|---|
| SW-AI-W06-data_structures_docker/README.md | 6.1KB | SKIP | Docker 환경 구축 가이드 |
| Data-Structures/README.md | 915B | SKIP | question sheet 안내 |
| Data-Structures/Memory_Experiments/EXPERIMENTS_INDEX.md | 2.2KB | SKIP | 실험 디렉터리 인덱스 |
| Data-Structures/Memory_Experiments/Virtual_Memory/README.md | 855B | SKIP | 실험 안내 |
| docs/ai-principles.md | 3.3KB | SKIP | 주차 AI 활용 원칙 |
| docs/c-pointer-reference-examples.md | 10KB | EDIT | CS 기초/C에서 Pointer 및 배열 → `cs-c-pointer-reference-examples.md` |
| docs/checklist.md | 3KB | SKIP | 주차 체크리스트 |
| docs/csapp-foundations-for-week6.md | 13.8KB | REWRITE | CS 기초/C 언어 기초 → `cs-c-and-csapp-foundations.md` (주차 표기 제거·제목 수정·학습 키워드 목차 재구성) |
| docs/goal-achievement.md, goal.md | 2~3KB | SKIP | 주차 목표 |
| docs/team-collaboration.md | 4.2KB | SKIP | 팀 협업 룰 |
| docs/week6-essential-systems-concepts.md | 14KB | REWRITE | Algorithm/자료구조 개요 → `algo-essential-systems-for-data-structures.md` (주차 표기 제거) |

### 4.4 W03-redis

| 파일 | 용량 | 판정 | 목적지 |
|---|---|---|---|
| README.md | 25KB | REWRITE | DB/Redis → `db-redis-architecture-and-features.md` (프로젝트 소개 섹션 제거, 학습 섹션만 유지) |
| docs/발표자료.md | 11.7KB | EDIT | DB/Redis → `db-redis-presentation-walkthrough.md` |
| docs/발표-치트시트.md | 9.3KB | EDIT | DB/Redis → `db-redis-live-demo-cheatsheet.md` |
| docs/cli-test-scenarios.md | 11.6KB | EDIT | DB/Redis → `db-redis-cli-test-scenarios.md` |
| .pytest_cache/README.md | 302B | SKIP | pytest |

### 4.5 W04-react

| 파일 | 용량 | 판정 | 목적지 |
|---|---|---|---|
| README.md | 17.8KB | REWRITE | 프로젝트 공통 지식/React → `proj-react-mini-react-guide.md` |
| docs/vdom.md | 688B | EDIT | 프로젝트 공통 지식/React → `proj-react-vdom-basics.md` |
| AGENTS.md | 381B | SKIP | 에이전트 지침 파일 |
| .github/pull_request_template.md | 826B | SKIP | PR 템플릿 |
| .codex/skills/commit-convention/SKILL.md | 3.9KB | SKIP | Codex 스킬 설정 |

### 4.6 W05-react

| 파일 | 용량 | 판정 | 목적지 |
|---|---|---|---|
| README.md | 11.5KB | REWRITE | 프로젝트 공통 지식/React → `proj-react-week5-runtime-overview.md` |
| learning-docs/overview.md | 6KB | KEEP | → `proj-react-runtime-overview.md` |
| learning-docs/renderer-and-vdom.md | 6.3KB | KEEP | → `proj-react-renderer-and-vdom.md` |
| learning-docs/runtime-walkthrough.md | 7.2KB | KEEP | → `proj-react-runtime-walkthrough.md` |
| learning-docs/app-showcase-guide.md | 10KB | KEEP | → `proj-react-app-showcase-guide.md` |
| docs/architecture.md | 12.3KB | EDIT | → `proj-react-architecture.md` (v3 표기 정리) |
| docs/api-spec.md | 11.2KB | EDIT | → `proj-react-api-spec.md` |
| docs/class-and-structure-diagram.md | 11.2KB | EDIT | → `proj-react-class-and-structure-diagram.md` |
| docs/requirements.md | 15.7KB | EDIT | → `proj-react-requirements.md` |
| docs/update-flow-and-scheduling.md | 7.2KB | KEEP | → `proj-react-update-flow-and-scheduling.md` |
| docs/demo-app-plan.md | 25.4KB | REWRITE | → `proj-react-demo-spa-design-case-study.md` (사례 연구로 재목차) |
| docs/week5-scope.md | 1.4KB | SKIP | v2→v3 범위 메모 |

### 4.7 W06-SQL

| 파일 | 용량 | 판정 | 목적지 |
|---|---|---|---|
| README.md | 10.7KB | REWRITE | DB/SQL 엔진 → `db-sql-engine-mini-processor-overview.md` |
| docs/architecture.md | 6.2KB | EDIT | DB/SQL 엔진 → `db-sql-engine-architecture-v1.md` |
| docs/system-design.md | 5.7KB | EDIT | DB/SQL 엔진 → `db-sql-engine-system-design.md` |
| docs/implementation-plan.md | 15.4KB | EDIT | DB/SQL 엔진 → `db-sql-engine-implementation-plan.md` |
| temp_readme2.md | 15KB | SKIP | README 대체본 (중복) |
| temp_week6_blog.md | 11.5KB | REWRITE | DB/SQL 엔진 → `db-sql-engine-command-line-processor-retrospective.md` (주차 표기 제거) |

### 4.8 W07-SQL (핵심 블록, 77 파일)

#### docs/ 최상위 6 개

| 파일 | 판정 | 목적지 |
|---|---|---|
| README.md | REWRITE | DB/SQL 엔진 → `db-sql-engine-minidb-overview.md` |
| 01-페이지-시스템.md | KEEP | DB/페이지 스토리지 → `db-page-storage-page-system.md` |
| 02-데이터-검색-과정.md | KEEP | DB/SQL 엔진 → `db-sql-engine-data-search-flow.md` |
| 03-B+Tree-인덱스-구조.md | KEEP | DB/B Tree B+ Tree → `db-bptree-index-structure.md` |
| 04-프레임-캐시-시스템.md | KEEP | DB/SQL 엔진 → `db-sql-engine-frame-cache.md` |
| 05-C-메모리-추상화-패턴.md | KEEP | CS 기초/C 언어 기초 → `cs-c-memory-abstraction-patterns.md` |
| 05-성능-테스트-가이드.md | KEEP | DB/SQL 엔진 → `db-sql-engine-performance-index-vs-scan.md` |

#### docs/blog/ README + 18 concepts + 10 applications + 9 legacy + 1 README

| 파일 | 판정 | 목적지 |
|---|---|---|
| blog/README.md | SKIP | 블로그 시리즈 인덱스 |
| blog/legacy/README.md | SKIP | legacy 시리즈 인덱스 |
| concepts/01-memory-hierarchy.md | KEEP | OS/Cache → `os-cache-memory-hierarchy.md` |
| concepts/02-cache-line-and-locality.md | KEEP | OS/Cache → `os-cache-line-and-locality.md` |
| concepts/03-virtual-memory-three-problems.md | KEEP | OS/가상 메모리 → `os-vm-three-problems.md` |
| concepts/04-page-table-and-pte.md | KEEP | OS/페이징 기법 → `os-paging-page-table-and-pte.md` |
| concepts/05-multi-level-page-table-and-mmu.md | KEEP | OS/페이징 기법 → `os-paging-multi-level-mmu.md` |
| concepts/06-tlb.md | KEEP | OS/TLB → `os-tlb-address-translation-cache.md` |
| concepts/07-page-fault-and-demand-paging.md | KEEP | OS/Page Fault → `os-page-fault-demand-paging.md` |
| concepts/08-copy-on-write.md | KEEP | OS/가상 메모리 → `os-vm-copy-on-write.md` |
| concepts/09-user-kernel-mode-and-syscall.md | KEEP | OS/System Call → `os-syscall-user-kernel-mode.md` |
| concepts/10-process-address-space.md | KEEP | OS/가상 메모리 → `os-vm-process-address-space.md` |
| concepts/11-task-struct-mm-struct-vma.md | KEEP | OS/가상 메모리 → `os-vm-task-struct-mm-struct-vma.md` |
| concepts/12-execve-and-program-loading.md | KEEP | OS/가상 메모리 → `os-vm-execve-and-program-loading.md` |
| concepts/13-fork-and-cow.md | KEEP | OS/가상 메모리 → `os-vm-fork-and-cow.md` |
| concepts/14-mmap-four-combinations.md | KEEP | OS/가상 메모리 → `os-vm-mmap-four-combinations.md` |
| concepts/15-brk-sbrk-and-heap.md | KEEP | Malloc lab/동적 메모리 할당 → `malloc-brk-sbrk-and-heap.md` |
| concepts/16-heap-allocator-internals.md | KEEP | Malloc lab/동적 메모리 할당 → `malloc-heap-allocator-internals.md` |
| concepts/17-memory-bugs-and-root-cause.md | KEEP | CS 기초/C에서 Pointer 및 배열 → `cs-c-memory-bugs-and-root-cause.md` |
| concepts/18-gc-runtime-memory-management.md | KEEP | CS 기초/Garbage Collect → `cs-gc-runtime-memory-management.md` |
| applications/01 .. 10 (10개) | KEEP | 아래 표 |
| legacy/01 .. 09 (9개) | SKIP | 모두 concepts/applications 의 예전 버전 |

**applications 10개 상세 목적지**

| 원본 | 목적지 |
|---|---|
| 01-db-page-equals-os-page-equals-bplus-node.md | DB/페이지 스토리지 → `db-page-storage-db-os-bplus-alignment.md` |
| 02-implementing-frame-cache-lru.md | DB/SQL 엔진 → `db-sql-engine-frame-cache-lru-implementation.md` |
| 03-page-type-tag-polymorphism.md | DB/페이지 스토리지 → `db-page-storage-type-tag-polymorphism.md` |
| 04-memcpy-replaces-serialization.md | DB/페이지 스토리지 → `db-page-storage-memcpy-serialization.md` |
| 05-slotted-page-internal-fragmentation.md | DB/페이지 스토리지 → `db-page-storage-slotted-internal-fragmentation.md` |
| 06-pread-pwrite-double-cache-doubt.md | DB/SQL 엔진 → `db-sql-engine-pread-pwrite-double-cache.md` |
| 07-bplus-tree-split-on-page-boundary.md | DB/B Tree B+ Tree → `db-bptree-split-on-page-boundary.md` |
| 08-reproducing-memory-bugs-on-purpose.md | CS 기초/C에서 Pointer 및 배열 → `cs-c-reproducing-memory-bugs.md` |
| 09-why-c-is-procedural.md | CS 기초/C 언어 기초 → `cs-c-why-procedural.md` |
| 10-vertical-integration-retrospective.md | DB/SQL 엔진 → `db-sql-engine-vertical-integration-retrospective.md` |

#### docs/sql/ 8 파일

| 파일 | 판정 | 목적지 |
|---|---|---|
| README.md | SKIP | 인덱스 |
| why-bptree-and-disk-pages.md | KEEP | DB/B Tree B+ Tree → `db-bptree-why-and-disk-pages.md` |
| page-structures-guide.md | KEEP | DB/페이지 스토리지 → `db-page-storage-structures-guide.md` |
| b-plus-tree-sql-plan.md | KEEP | DB/SQL 엔진 → `db-sql-engine-bptree-plan.md` |
| implementation-spec.md | EDIT | DB/SQL 엔진 → `db-sql-engine-implementation-spec.md` |
| sql-feature-scope-roadmap.md | EDIT | DB/SQL 엔진 → `db-sql-engine-feature-scope-roadmap.md` |
| system-perspective-guide.md | KEEP | DB/SQL 엔진 → `db-sql-engine-system-perspective-guide.md` |
| week7-bptree-sql-blueprint.md | REWRITE | DB/SQL 엔진 → `db-sql-engine-bptree-blueprint.md` (week7 표기 제거) |

#### docs/convention/ 4 파일

| 파일 | 판정 | 목적지 |
|---|---|---|
| c-style.md, python-style.md, commit-convention.md, project-structure.md | SKIP | 팀 컨벤션, 별도 workspace/skills 에 존재 |

#### docs/csapp-ch9-virtual-memory/

| 파일 | 판정 | 목적지 |
|---|---|---|
| csapp-ch9-keyword-tree.md | SKIP | 31KB 키워드 트리 원안 → 이미 tree.yaml 에 반영 |

#### docs/questions/ 25 + presentation-groups/ 4

| 파일 | 판정 | 목적지 |
|---|---|---|
| q01-va-pa.md | KEEP | OS/페이징 기법 → `os-paging-q01-va-vs-pa.md` |
| q02-page-cacheline-word.md | KEEP | OS/Cache → `os-cache-q02-page-cacheline-word.md` |
| q03-page-size-4kb.md | KEEP | OS/페이징 기법 → `os-paging-q03-page-size-4kb.md` |
| q04-resident-not-resident.md | KEEP | OS/가상 메모리 → `os-vm-q04-resident-vs-not-resident.md` |
| q05-page-fault.md | KEEP | OS/Page Fault → `os-page-fault-q05-classification.md` |
| q06-global-variable-lifecycle.md | KEEP | OS/가상 메모리 → `os-vm-q06-global-variable-lifecycle.md` |
| q07-vma-vs-page-table.md | KEEP | OS/가상 메모리 → `os-vm-q07-vma-vs-page-table.md` |
| q08-memory-protection.md | KEEP | OS/Page Fault → `os-page-fault-q08-memory-protection-bits.md` |
| q09-cow.md | MERGE → concepts/08-copy-on-write (짧음) 단, 문제지 형태 보존가치 있으므로 KEEP | OS/가상 메모리 → `os-vm-q09-cow.md` |
| q10-vpn-offset.md | KEEP | OS/페이징 기법 → `os-paging-q10-vpn-offset.md` |
| q11-page-table-pipeline.md | KEEP | OS/페이징 기법 → `os-paging-q11-pipeline.md` |
| q12-cr3-page-sharing.md | KEEP | OS/페이징 기법 → `os-paging-q12-cr3-page-sharing.md` |
| q13-tlb.md | MERGE → concepts/06-tlb (691B 너무 짧음) | concepts 로 흡수, 개별 파일 생성 X |
| q14-multi-level-page-table.md | KEEP | OS/페이징 기법 → `os-paging-q14-multi-level.md` |
| q15-mmap.md | MERGE → concepts/14-mmap (763B) | 개별 파일 생성 X |
| q16-sbrk-vs-mmap.md | MERGE → concepts/15-brk-sbrk (735B) | 개별 파일 생성 X |
| q17-os-kernel-process-thread.md | KEEP | OS/Process와 Thread → `os-process-q17-os-kernel-scheduler-relation.md` |
| q18-kernel-mode-entry.md | MERGE → concepts/09-user-kernel-syscall (759B) | 개별 파일 생성 X |
| q19-fragmentation.md | KEEP | Malloc lab/Fragmentation → `malloc-q19-internal-vs-external.md` |
| q20-segregated-free-list.md | KEEP | Malloc lab/seglist → `malloc-q20-segregated-free-list.md` |
| q21-header-lower-3bits.md | KEEP | Malloc lab/동적 메모리 할당 → `malloc-q21-header-lower-3bits.md` |
| q22-split-coalesce.md | KEEP | Malloc lab/Coalescing → `malloc-q22-split-and-coalesce.md` |
| q23-placement-policy.md | KEEP | Malloc lab/할당 정책 → `malloc-q23-placement-policy.md` |
| q24-free-design.md | KEEP | Malloc lab/동적 메모리 할당 → `malloc-q24-free-design-philosophy.md` |
| q25-memory-bugs.md | KEEP | CS 기초/C에서 Pointer 및 배열 → `cs-c-q25-memory-bugs.md` |
| presentation-groups/presenter-hojun-process-kernel-mapping.md | EDIT | OS/가상 메모리 → `os-vm-presentation-process-kernel-mapping.md` |
| presentation-groups/presenter-hyunho-paging-fault-protection.md | EDIT | OS/페이징 기법 → `os-paging-presentation-fault-protection.md` |
| presentation-groups/presenter-youngbin-address-translation-basics.md | EDIT | OS/페이징 기법 → `os-paging-presentation-address-translation-basics.md` |
| presentation-groups/presenter-woonyong-allocator-and-memory-bugs.md | REWRITE | Malloc lab/동적 메모리 할당 → `malloc-presentation-allocator-and-memory-bugs.md` (45KB, 섹션 재편집) |

### 4.9 W07-malloc-lab

| 파일 | 판정 | 목적지 |
|---|---|---|
| SW_AI-W07-malloc-lab/README.md | SKIP | Docker 환경 구축 |
| malloc-lab/README.md | EDIT | Malloc lab/동적 메모리 할당 → `malloc-lab-working-guide.md` |

### 4.10 W08-SQL (43 파일)

#### 최상위·convention

| 파일 | 판정 |
|---|---|
| README.md (9B) | SKIP |
| docs/README.md | SKIP |
| docs/convention/{c-style, python-style, commit-convention, project-structure, codex-skill-guide}.md | SKIP (W07 과 중복 + 팀 운영) |

#### docs/csapp-11/ 9 파일

| 파일 | 판정 | 목적지 |
|---|---|---|
| README.md | SKIP | 인덱스 |
| 00-roadmap-overview.md | SKIP | 주차 로드맵 |
| 01-week-plan.md | SKIP | 주간 실행 계획 |
| 02-keyword-tree.md | SKIP | tree.yaml 에 이미 반영 |
| 03-completion-rubric.md | SKIP | 학습 완료 판단표 |
| 04-sql-api-implementation-bridge.md | EDIT | 네트워크/Tiny 웹서버 → `net-tiny-sql-api-implementation-bridge.md` |
| 05-ch11-sequential-numeric-walkthrough.md | REWRITE | 네트워크/HTTP 프로토콜 → `net-http-csapp11-sequential-walkthrough.md` (43KB 대형, 헤더 정리) |
| 06-resources.md | SKIP | 참고 링크 모음 |
| 07-ch11-code-reference.md | EDIT | 네트워크/소켓 시스템콜 → `net-socket-csapp11-code-reference.md` |

#### docs/question/ 3 파일

| 파일 | 판정 |
|---|---|
| 00-team-question-list.md | SKIP | 팀 질문 집계 |
| q11-page-table-pipeline-example.md | SKIP | "예시 문서" 형식, q11 본문과 중복 |
| q12-socket-connection-lifecycle.md | SKIP | 1KB, incomplete |

#### docs/team/ 팀원별

| 파일 | 판정 | 목적지 |
|---|---|---|
| choihyunjin1/06_choihyunjin1_followup_questions.md | EDIT | 네트워크/HTTP 프로토콜 → `net-http-csapp11-followup-questions.md` (75KB, 저자 credit 본문에 명시 유지) |
| hojun-lee99/questions.md | SKIP | 336B, 완성되지 않은 질문 리스트 |
| huiugim8-wq/q01-write-kernel-send-path.md | EDIT | 네트워크/소켓 내부 구조 → `net-socket-internals-kernel-send-path.md` |
| iamnuked/Q.md | SKIP | 1KB 개인 메모 |
| iamnuked/SECRET_FILE.md | SKIP | 개인 문서 (DON'T EDIT 표기) |
| w00jinLee/questions.md | SKIP | 1.8KB, 짧은 질문 |

#### docs/team/woonyong-kr/ 24 파일

| 파일 | 판정 | 목적지 |
|---|---|---|
| README.md | SKIP | 문서 인덱스 |
| 00-topdown-walkthrough.md | EDIT | 네트워크/소켓 내부 구조 → `net-socket-topdown-walkthrough.md` |
| 99-whiteboard-session.md | EDIT | 네트워크/Tiny 웹서버 → `net-tiny-whiteboard-session-design.md` |
| q01-network-hardware.md | KEEP | 네트워크/네트워크 하드웨어 → `net-hw-ethernet-bridge-router-lan-wan.md` |
| q02-ip-address-byte-order.md | KEEP | 네트워크/IP와 DNS → `net-ip-address-byte-order.md` |
| q03-dns-domain-cloudflare.md | KEEP | 네트워크/IP와 DNS → `net-dns-domain-cloudflare.md` |
| q04-filesystem.md | EDIT | OS/System Call → `os-syscall-linux-filesystem-deep-dive.md` (26KB, VFS 주제) |
| q05-socket-principle.md | KEEP | 네트워크/소켓 내부 구조 → `net-socket-principle-hw-sw.md` |
| q06-ch11-4-sockets-interface.md | KEEP | 네트워크/소켓 시스템콜 → `net-socket-csapp11-4-interface.md` |
| q07-tcp-udp-socket-syscall.md | KEEP | 네트워크/전송 계층 TCP UDP → `net-tcp-udp-socket-syscall.md` |
| q08-host-network-pipeline.md | KEEP | 네트워크/소켓 내부 구조 → `net-socket-host-send-pipeline.md` |
| q09-network-cpu-kernel-handle.md | KEEP | 네트워크/I/O Bridge와 NIC → `net-io-bridge-cpu-kernel-handle-lens.md` |
| q10-io-bridge.md | KEEP | 네트워크/I/O Bridge와 NIC → `net-io-bridge-physical-kernel-path.md` |
| q11-http-ftp-mime-telnet.md | KEEP | 네트워크/HTTP 프로토콜 → `net-http-ftp-mime-telnet-comparison.md` |
| q12-tiny-web-server.md | KEEP | 네트워크/Tiny 웹서버 → `net-tiny-csapp11-6-functions-and-routines.md` |
| q13-cgi-fork-args.md | KEEP | 네트워크/CGI 동적 처리 → `net-cgi-fork-args-passing.md` |
| q14-echo-server-datagram-eof.md | KEEP | 네트워크/전송 계층 TCP UDP → `net-tcp-udp-echo-server-datagram-eof.md` |
| q15-proxy-extension.md | KEEP | 네트워크/프록시 서버 → `net-proxy-tiny-extension.md` |
| q16-thread-pool-async.md | KEEP | 네트워크/Concurrent Server → `net-concurrent-thread-pool-async.md` |
| q17-concurrency-locks.md | KEEP | 네트워크/서버 동시성과 락 → `net-server-concurrency-thread-pool-locks.md` |
| q18-thread-concurrency.md | KEEP | 네트워크/서버 동시성과 락 → `net-server-thread-concurrency-without-locks.md` |
| q19-process-ancestry-fd-inheritance.md | EDIT | OS/Process와 Thread → `os-process-ancestry-fd-inheritance.md` (주차 표기 제거) |
| q20-fd-lifecycle-and-dispatch.md | EDIT | 네트워크/소켓 내부 구조 → `net-socket-fd-lifecycle-and-dispatch.md` |
| q21-process-parent-and-memory-deep-dive.md | EDIT | OS/가상 메모리 → `os-vm-process-parent-heap-mmap-demand-paging.md` |

### 4.11 W08-webproxy_lab

| 파일 | 판정 |
|---|---|
| README.md | SKIP | Docker 환경 가이드 |
| webproxy-lab/README.md | SKIP | CSAPP Proxy lab 원본 배포 |

## 5. 최종 수량 요약

| 구분 | 파일 수 |
|---|---|
| KEEP (원문 + 프런트매터만) | 62 |
| EDIT (소폭 정리) | 19 |
| REWRITE (섹션 재구성) | 10 |
| MERGE (다른 포스트로 흡수) | 4 |
| SKIP (지식 트리 미포함) | 94 |
| 합계 | 189 |

최종 포스트 개수: **91** (KEEP 62 + EDIT 19 + REWRITE 10)

## 6. 프런트매터 규약 (공통)

```yaml
---
title: "<원본 H1 정리안>"
category: "<L0 이름 정확히>"
keyword: "<L1 이름 정확히>"
subkeyword: "<L2 이하 폴더 이름>"   # L2 이하 폴더 안 포스트인 경우에만, 가장 구체적인 폴더명
created: "2026-04-20"                # 필수, YYYY-MM-DD, 수기 입력
updated: "2026-04-20"                # 필수, YYYY-MM-DD, 수기 입력
source: "krafton-jungle/<주차 디렉터리>/<상대 경로>"
---
```

- `created`, `updated` 는 CONTRIBUTING.md 4.3 절 에 따라 **필수** 필드다. 이관 시점엔 `created == updated` 로 두고, 이후 실질 수정이 있을 때만 `updated` 를 올린다.
- EDIT·REWRITE 대상은 본문 시작부의 주차·프로젝트·AI 관련 메타 문장을 제거한다. 이모지는 본문에서 제거한다.
- KEEP 포함한 모든 포스트는 `/Users/woonyong/workspace/skills/tech-blog-writing/SKILL.md` 의 금지 패턴 체크리스트를 통과해야 한다(이모지·강조어·강사 톤·AI 흔적·알고리즘 문제 풀이 금지).
- REWRITE·SPLIT 대상은 동 스킬의 10단계 구조로 재구성한다.
- SPLIT 결과 생성된 복수 포스트는 각자 "같은 원본에서 나온 다른 포스트" 를 참고 섹션에 상호 링크한다.

## 7. 작업 실행 순서 (승인 후)

1. `docs/tree.yaml` 섹션 3.1–3.7 적용 (L1 추가·조정).
2. 3.8 절 응답에 따라 `sub` 문자열을 객체로 승격 (L2 폴더 생성 선언). L2 아래가 또 승격 대상이면 객체 `sub` 로 재귀 구성.
3. 3.10 절 에 따라 알고리즘 문제 풀이 원본은 배제, 4 절 표에서 해당 행은 SKIP 상태 유지.
4. 3.11 절 승인 결과에 따라 PDF 기반 신규 L1·sub 를 `tree.yaml` 에 병합.
5. `make scaffold` 로 새 L1/L2 이하 폴더·README 생성.
6. `make validate` 로 고아 폴더·마커 구성 확인.
7. KEEP/EDIT/REWRITE 파일을 각 목적지에 복사·편집 (KEEP 포함해 `tech-blog-writing` 스킬의 금지 패턴 체크리스트 통과 필수).
8. SPLIT 대상 원본을 `tech-blog-writing` 스킬의 분할 절차에 따라 분할·재작성, 각 조각을 L2 이하 폴더로 이동.
9. MERGE 파일 처리 (대상 포스트에 섹션 추가).
10. 각 포스트 프런트매터에 `created`/`updated` 를 `YYYY-MM-DD` 로 수기 기입.
11. `make validate && make build` 최종 통과.
12. `scan-state.yaml` 을 갱신 (`docs`, `_krafton` 의 `last_scanned_at` 을 작업 종료 시각으로 기록).
13. 커밋 (commit-convention 준수, AI 흔적·이모지 금지). `.gitignore` 가 이미 `docs/` 외를 제외하므로 별도 조치 불필요.

## 8. 승인 체크리스트

다음 항목에 하나씩 Y/N 또는 수정 의견을 주시면 바로 착수합니다.

1. 카테고리 경계 매트릭스(2.1) 그대로 진행?
2. 네트워크 카테고리에 L1 7개 추가(3.4) 그대로 진행? 혹은 기존 L1 흡수·통합?
3. DB 카테고리에 L1 3개(Redis / 페이지 스토리지 / SQL 엔진) 추가 그대로?
4. OS `가상 메모리` sub 확장(3.5) 그대로?
5. 3.8 절 L2 폴더 승격 대상 표의 각 행에 대한 Y / N / 일부.
6. 3.10 절 알고리즘 문제 풀이 배제 정책 그대로 진행?
7. 3.11.1 CSAPP PDF 기반 신규 L1 (어셈블리 언어 기초 / 프로그램 성능 최적화 / 링커와 로더 / 예외 제어 흐름) 승인?
8. 3.11.2 PINTOS 특강 PDF 기반 `C 언어 기초` sub 확장 승인?
9. 3.11.3 Web to MSA PDF 기반 L1 신설 (HTTP 프로토콜 sub 확장 / 동적 처리 모델 진화 / 서버 아키텍처 패턴 / 아키텍처 패턴) 승인? 승인 시 3.4 절 `CGI 동적 처리` L1 흡수 여부도 함께 회신.
10. SKIP 94 파일 중 살려야 할 항목이 있는지? (특히 convention/c-style, python-style 등)
11. `_krafton/` 최종 정리 후 삭제? 혹은 로컬 보관? (신 `.gitignore` 하에 로컬 보관은 문제 없음)
12. `docs/merge-plan.md` 자체를 원격 커밋 포함? 아니면 `.gitignore` 로 로컬 전용 처리? (현재는 `docs/` 허용 규칙으로 원격에 포함되는 상태)
13. `scan-state.yaml` 의 초기값(null) 을 그대로 두고 다음 스캔 시 Claude 가 타임스탬프를 기록하게 할지, 또는 지금 즉시 `docs`, `_krafton` 을 전수 스캔으로 간주해 현재 시각을 기입할지?
