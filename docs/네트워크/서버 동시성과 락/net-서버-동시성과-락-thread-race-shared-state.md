---
title: 멀티코어 공유 메모리 — MESI 는 왜 race 를 막지 못하는가
category: 네트워크
keyword: 서버 동시성과 락
created: 2026-04-20
updated: 2026-04-20
tags: [mesi, cache-coherence, race-condition, atomic, rcu, false-sharing, tsan]
summary: 하드웨어의 캐시 일관성(MESI) 이 있어도 락 없는 코드가 왜 터지는지, 실전 시나리오 몇 가지로 분해합니다. Lost Update·Torn Write·UAF·False Sharing 같은 패턴과 커널 locking 카탈로그를 정리합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q18-thread-concurrency.md
---

# 멀티코어 공유 메모리 — MESI 는 왜 race 를 막지 못하는가

"스레드는 주소 공간을 공유하는 가벼운 프로세스" 입니다. 리눅스에서는 `CLONE_VM` 플래그 유무로만 구분되고, `mm_struct`·`files_struct`·시그널 핸들러 테이블을 공유합니다. 이 공유가 편의이자 위험의 근원입니다.

## 하드웨어 — MESI 캐시 일관성

코어가 N 개면 L1·L2 캐시도 각자입니다. 같은 DRAM 주소의 데이터가 정합성을 유지하도록 코어 간 버스에서 주고받는 프로토콜이 MESI 입니다.

| 상태 | 의미 | DRAM 과 | 다른 코어에 |
|---|---|---|---|
| M Modified | 내가 수정했고 나만 가짐 | 다름 (stale) | 없음 |
| E Exclusive | 나만 가짐, 아직 안 씀 | 같음 | 없음 |
| S Shared | 여럿이 읽기 공유 | 같음 | 있음 |
| I Invalid | 무효 | — | — |

전이 예시입니다.

```text
(A) 둘 다 읽기만
    Core0: X 로드 -> E
    Core1: X 로드 -> bus 로 snoop -> 둘 다 S

(B) Core0 가 쓰려 함
    Core0: "RFO(X)" 브로드캐스트 -> Core1 의 X 라인 I
    Core0: S -> M, write-back 은 나중

(C) 무효화된 Core1 이 다시 쓰려 함
    Core1: I -> bus 요청 -> Core0 의 M 라인을 cache-to-cache 포워딩
    Core0: M -> I, Core1: M
```

MESI 메시지는 Intel 의 Ring/Mesh, AMD 의 Infinity Fabric, 대형 서버의 Directory-based 일관성 버스 위에서 오갑니다. "CPU 끼리 통신하지 않는다" 는 오해와 달리 수십~수백 사이클을 들여 통신합니다.

## MESI 가 있어도 레지스터 경계는 보호되지 않는다

이것이 락이 필요한 이유의 핵심입니다. `count++` 은 어셈블리로 세 단계입니다.

```asm
mov eax, [count]    ; load
inc eax             ; compute
mov [count], eax    ; store
```

두 코어가 동시에 실행하면 다음이 일어납니다.

```text
t=0 Core0: mov eax,[count]  ; eax=100
t=0 Core1: mov eax,[count]  ; eax=100
t=1 Core0: inc eax          ; eax=101
t=1 Core1: inc eax          ; eax=101
t=2 Core0: mov [count],eax  ; 캐시 RFO, [count]=101
t=2 Core1: mov [count],eax  ; 캐시 RFO, [count]=101

결과: count=101 (102 가 되어야 하는데 한 번 소실)
```

MESI 는 "마지막 store 가 이긴다" 만 보장할 뿐 load-compute-store 시퀀스를 원자적으로 묶어 주지 않습니다. 사이에 다른 코어가 끼어들 틈이 있습니다.

## 락 없이 터지는 시나리오

### Lost Update — 카운터 경쟁

```c
int request_count = 0;
void *handler(void *arg) {
    request_count++;     /* 1만 번 호출 */
    return NULL;
}
```

실행할 때마다 결과가 다릅니다. 크래시는 아니지만 데이터 정합성이 깨져 과금·통계·재고 시스템에선 치명적입니다.

수정은 atomic RMW 로 감싸는 것입니다.

```c
atomic_int request_count = 0;
atomic_fetch_add(&request_count, 1);
```

### Torn Write — 찢어진 64비트 값

32비트 시스템에서 64비트 정수를 공유할 때, reader 가 상위 32비트는 새 값, 하위 32비트는 옛 값인 괴상한 값을 받을 수 있습니다. x86-64 도 정렬되지 않은 64비트 값은 같은 문제를 겪습니다. `_Atomic uint64_t` 로 감싸야 안전합니다.

### Use-After-Free — 삭제와 참조 경쟁

```c
void *reader(void *arg) {
    struct session *s = sessions[id];   /* 포인터 load */
    if (s) printf("%s\n", s->data);      /* 역참조 */
}
void *deleter(void *arg) {
    struct session *s = sessions[42];
    sessions[42] = NULL;
    free(s);                             /* reader 가 이미 포인터를 복사했을 수 있음 */
}
```

reader 가 포인터를 복사한 뒤 deleter 가 free 하면 역참조가 해제된 메모리를 건드립니다. 크래시 또는 조용한 메모리 손상으로 이어집니다. 수정은 reference count + atomic 또는 RCU 입니다.

### False Sharing — 크래시 아닌 성능 지옥

```c
struct stats {
    long counter_a;   /* Thread A 가 계속 쓰기 */
    long counter_b;   /* Thread B 가 계속 쓰기 */
} s;                   /* 둘 다 같은 64B 캐시 라인 */
```

논리적으로 독립인데 매 쓰기가 상대 라인을 invalidate 시켜 성능이 1/10 이하로 떨어집니다. 수정은 패딩 또는 cacheline 정렬입니다.

```c
struct stats {
    long counter_a;
    char pad[64 - sizeof(long)];
    long counter_b;
} __attribute__((aligned(64)));
```

### 기타 자주 터지는 패턴

- TOCTOU — 체크와 사용 사이에 상태가 바뀝니다. 파일·세션 존재 확인 후 사용하는 코드가 대표적입니다.
- thread-unsafe 함수 — `strtok`·`localtime`·`gethostbyname` 의 내부 static 버퍼. `_r` 버전으로 교체합니다.
- malloc 경합 — glibc `ptmalloc` 의 메인 아레나 락이 병목이 됩니다. jemalloc·tcmalloc 는 per-thread cache 로 완화합니다.
- Signal 재진입 — 핸들러 안에서 `malloc` 호출은 heap 락을 재귀로 잡으려 해 데드락이 납니다. async-signal-safe 함수만 써야 합니다.

## 리눅스 커널 locking 카탈로그

커널이 제공하는 동기화 수단은 상황에 따라 엄격히 구분됩니다.

| 종류 | 특성 | 언제 |
|---|---|---|
| `atomic_t` | 단일 정수 RMW 원자 | 카운터·플래그 |
| `spinlock_t` | busy-wait, 인터럽트 안전 | IRQ·softirq, 짧은 구역 |
| `rwlock_t` | reader 다수 / writer 단일 | 읽기 주도 |
| `seqlock_t` | writer 우선, reader 재시도 | jiffies·시간 |
| `mutex` | sleep 가능 | 프로세스 컨텍스트, 긴 구역 |
| `semaphore` | counting, sleep | 자원 개수 제한 |
| `rw_semaphore` | sleep 가능 reader/writer | mmap_sem 등 |
| `completion` | 한 번의 이벤트 대기 | I/O 완료 |
| RCU | reader lock-free, writer copy-update | 라우팅 테이블·dentry cache |

의사결정 트리는 다음과 같습니다.

```text
임계 구역에서 sleep 가능한가?
 - Yes -> mutex / rwsem / semaphore
         (읽기 압도적이면 rwsem 또는 RCU)
 - No (IRQ/softirq)
     - 짧고 단순: spinlock (IRQ-safe: spin_lock_irqsave)
     - 매우 읽기 위주: seqlock 또는 RCU
     - 단일 정수: atomic_t
```

RCU 는 읽기를 lock-free 로 유지하고 writer 가 copy-update 한 뒤 `synchronize_rcu()` 로 old 를 정리하는 기법입니다. dentry cache·routing table 처럼 쓰기가 드문 공유 자료구조에서 최고 성능을 냅니다.

## 유저 공간 도구 비교

| 도구 | 용도 |
|---|---|
| `pthread_mutex_t` / `pthread_rwlock_t` | POSIX 기본 |
| C11 `_Atomic`, `<stdatomic.h>` | 이식성 있는 원자 연산 |
| `std::mutex`, `std::atomic` | C++ |
| `java.util.concurrent` | JVM |
| Go `sync.Mutex`, `atomic` | Go |
| Python `threading.Lock` + GIL | 바이트코드 단위 원자, 다만 복합 연산은 여전히 race |

## 검증 도구

동시성 버그는 재현이 어려우므로 도구로 보조해야 합니다.

- ThreadSanitizer (TSan) — data race 동적 검출. `-fsanitize=thread`. CI 필수.
- Helgrind·DRD (Valgrind) — race·lock order 위반.
- AddressSanitizer (ASan) — use-after-free·double-free.
- lockdep·KCSAN — 커널 버전의 동일 도구.

## 체크리스트

- 공유 자료구조와 락을 1:1 로 연결했나 (어떤 락이 어떤 필드를 지키는지 주석)
- 여러 락의 획득 순서가 코드 전체에서 일관된가
- RMW 연산을 atomic 이나 락으로 감쌌나
- 긴 I/O 는 락 밖으로 빼냈나
- 시그널 핸들러에서 async-signal-unsafe 함수를 안 부르나
- `fork()` 이후 child 에서 락 상태가 정리되는가
- TSan 이 녹색인가
- 읽기 압도적 자료는 RWLock 또는 RCU 로 바꿀 수 있나
- 핫 변수는 cacheline 분리했나

## 요점

MESI 가 캐시 일관성을 보장하더라도 load-compute-store 경계까지 원자화해 주지는 않습니다. 그래서 공유 메모리에는 반드시 원자 연산 또는 락이 필요하고, 접근 패턴(카운터·읽기 압도·순서 민감) 에 맞는 프리미티브를 선택해야 합니다. 멀티코어 시대의 "공짜 점심" 은 없고, 대신 프리미티브를 제대로 고르면 충돌 비용을 최소로 낮출 수 있습니다.
