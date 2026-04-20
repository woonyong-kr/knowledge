---
title: 서버 동시성과 락 — mutex·condvar·semaphore·RWLock 의 실전 배치
category: 네트워크
keyword: 서버 동시성과 락
created: 2026-04-20
updated: 2026-04-20
tags: [mutex, condvar, semaphore, rwlock, race-condition, thread-safe, deadlock]
summary: 스레드 풀 서버에서 공유 자원마다 어떤 락을 쓰는지 정리합니다. job queue 는 세마포어, 커넥션 풀은 mutex+condvar, 캐시는 RWLock, 통계 카운터는 atomic. thread-safe 와 reentrant 의 차이, 데드락 회피 규칙도 함께 다룹니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q17-concurrency-locks.md
---

# 서버 동시성과 락 — mutex·condvar·semaphore·RWLock 의 실전 배치

스레드 풀 서버는 단일 스레드 서버가 아닙니다. 여러 worker 가 같은 자료구조를 동시에 만지는 순간 race condition·데드락·캐시 일관성 문제가 생깁니다. 상황마다 어떤 락을 써야 하는지가 동시성 설계의 본론입니다.

## 락이 필요한 이유

단일 스레드면 문제가 없습니다. 여러 스레드가 같은 자료구조를 동시에 만지는 순간 문제가 발생합니다. `count++` 조차 세 개 명령으로 쪼개져 실행됩니다.

```text
(1) load   count  -> 레지스터
(2) add    1      -> 레지스터
(3) store  레지스터 -> count

두 스레드가 100 -> 102 로 올리려 할 때:
  A: load  (reg=100)
  B: load  (reg=100)     <- A 가 쓰기 전
  A: store (count=101)
  B: store (count=101)   <- 한 번의 증가가 사라짐
```

해결책은 해당 코드 블록을 한 번에 한 스레드만 지나가게 직렬화하는 것이고, 그 도구가 락입니다.

## 세 가지 프리미티브

- mutex — "한 번에 하나만". lock → 임계 구역 → unlock.
- condvar — "할 일 없으면 자고 있어, 생기면 깨워줘". mutex 와 함께 씁니다.
- semaphore — "카운트 가능한 락". P(내리기, 0 이면 대기), V(올리기, 자는 사람 깨움).

condvar 의 패턴은 다음과 같습니다.

```c
/* consumer */
lock();
while (queue_empty)
    cond_wait(&not_empty, &lock);   /* 잠듦 */
take_item();
unlock();

/* producer */
lock();
put_item();
cond_signal(&not_empty);             /* 자는 스레드 하나 깨움 */
unlock();
```

`while (조건) cond_wait` 은 반드시 `if` 가 아닌 `while` 로 감싸야 합니다. spurious wakeup 이나 다른 스레드가 먼저 집어가는 경우에도 조건이 유지됨을 보장하기 위함입니다.

세마포어는 카운터 하나로 같은 일을 더 간결하게 합니다. CSAPP 의 `sbuf` 는 세마포어 세 개로 job queue 를 구현합니다.

```c
typedef struct {
    int *buf;
    int n, front, rear;
    sem_t mutex;   /* 상호 배제 */
    sem_t slots;   /* 빈 슬롯 수 */
    sem_t items;   /* 채워진 슬롯 수 */
} sbuf_t;

void sbuf_insert(sbuf_t *sp, int item) {
    P(&sp->slots);
    P(&sp->mutex);
    sp->buf[(++sp->rear) % sp->n] = item;
    V(&sp->mutex);
    V(&sp->items);
}
```

## thread-safe 와 reentrant

thread-unsafe 함수는 내부에 전역 static 버퍼를 써서 두 스레드가 동시에 부르면 서로 덮어씁니다. `strtok`·`localtime`·`gethostbyname` 이 대표적이며 스레드 풀에서는 금지입니다.

thread-safe 함수는 내부에 락이 있거나 공유 상태가 없어 동시 호출이 안전합니다. `malloc`·`printf`·`pthread_*`·`getaddrinfo` 등입니다.

reentrant 함수는 더 엄격한 버전으로 시그널 핸들러 안에서도 안전합니다. 공유 상태를 전혀 안 쓰고 인자로 모든 상태를 받는 `_r` 접미사 함수들입니다.

| 안 됨 | 안전한 대체 |
|---|---|
| `strtok` | `strtok_r` |
| `localtime` | `localtime_r` |
| `asctime` | `asctime_r` |
| `gethostbyname` | `getaddrinfo` |
| `rand` | `rand_r` / `random_r` |

`errno` 는 POSIX 에서 per-thread 변수이므로 걱정하지 않아도 됩니다.

## 데드락 회피

두 스레드가 서로가 쥔 락을 기다리면 영원히 멈춥니다. 회피의 핵심은 락 획득 순서 고정입니다. 주소 순서를 규칙으로 쓰는 방법이 가장 보편적입니다.

```c
void safe_acquire_two(pthread_mutex_t *a, pthread_mutex_t *b) {
    if (a < b) { pthread_mutex_lock(a); pthread_mutex_lock(b); }
    else       { pthread_mutex_lock(b); pthread_mutex_lock(a); }
}
```

예방 네 원칙은 다음과 같습니다.

1. 가능한 한 락 하나만 잡는다.
2. 여러 개 잡아야 하면 모든 스레드가 동일한 순서로.
3. 락 안에서 네트워크·디스크 I/O 같은 오래 걸리는 일 금지.
4. 락 중첩을 피하고, 어쩔 수 없으면 순서를 문서화한다.

## RWLock 과 atomic

read 가 압도적으로 많은 자료구조(프록시 캐시·DNS 캐시·설정 테이블) 에서는 RWLock 이 뮤텍스보다 훨씬 빠릅니다. 여러 reader 가 동시에 읽을 수 있고, writer 는 혼자만 잡습니다.

```c
pthread_rwlock_t cache_lock;
pthread_rwlock_rdlock(&cache_lock);  /* 여러 reader 동시 */
pthread_rwlock_wrlock(&cache_lock);  /* writer 혼자 */
```

단일 변수 카운터에는 락 대신 atomic 이 훨씬 싸고 간단합니다.

```c
#include <stdatomic.h>
atomic_int request_count = 0;
atomic_fetch_add(&request_count, 1);
```

## 실전 배치 — 서버의 여섯 공유 지점

하나의 요청을 처리하면서 worker 가 만지는 공유 자원들과 각각에 맞는 락을 지도처럼 정리하면 다음과 같습니다.

```text
main -- accept -- sbuf_insert(jobs)    <- 세마포어 3개
           |
       job queue
           | sbuf_remove
       worker1..N
           ├ HTTP 파싱
           ├ DB 커넥션 획득             <- mutex + condvar
           ├ SQL 실행 (blocking)
           ├ DB 커넥션 반납             <- mutex + condvar
           ├ 통계 카운터 ++              <- atomic
           ├ 캐시 조회/갱신             <- RWLock
           ├ 로그 기록                  <- mutex 또는 atomic write
           ├ HTTP 응답 write
           └ close(connfd)
```

커넥션 풀의 전형적 구현은 다음과 같습니다.

```c
typedef struct {
    DBConn *conns[POOL_SIZE];
    int count;
    pthread_mutex_t lock;
    pthread_cond_t  available;
} ConnPool;

DBConn *pool_get(ConnPool *p) {
    pthread_mutex_lock(&p->lock);
    while (p->count == 0)
        pthread_cond_wait(&p->available, &p->lock);
    DBConn *c = p->conns[--p->count];
    pthread_mutex_unlock(&p->lock);
    return c;
}

void pool_put(ConnPool *p, DBConn *c) {
    pthread_mutex_lock(&p->lock);
    p->conns[p->count++] = c;
    pthread_cond_signal(&p->available);
    pthread_mutex_unlock(&p->lock);
}
```

로그는 mutex + `fflush` 로 감싸거나, PIPE_BUF(4096B) 이하 한 줄은 `write()` 한 번으로 POSIX atomic 이 보장되는 특성을 활용합니다.

```c
char line[1024];
int n = snprintf(line, sizeof line, "[%ld] %s\n", time(NULL), msg);
write(log_fd, line, n);   /* PIPE_BUF 이하면 atomic */
```

시그널은 main 만 받게 하는 것이 정석입니다. worker 생성 전에 블록해 두고 main 이 `sigwait` 로 동기 처리합니다. `SIGPIPE` 는 서버에서는 반드시 무시해 끊긴 소켓에 write 할 때 프로세스가 죽지 않게 합니다.

```c
signal(SIGPIPE, SIG_IGN);
```

## 실전 체크리스트

- 공유 자료구조(큐·풀·캐시·로그)마다 어떤 락을 쓸지 결정했나
- 락 안에서 blocking I/O 를 하고 있지는 않은가
- 두 락을 잡는 코드가 있으면 순서 규칙이 있는가
- `strtok`·`localtime` 같은 unsafe 함수를 안 쓰나
- worker 는 `pthread_detach` 로 자동 회수되는가
- `SIGPIPE` 를 무시하고 있는가
- `connfd` 를 정확히 한 번만 close 하나 (worker 가 책임)

## 스레드 풀의 상한

워커 수를 무작정 늘린다고 빨라지지 않습니다. CPU 코어 수, 락 경합 증가, 메모리 스택(기본 8MB × N) 세 가지 상한이 있습니다. 경험적으로 I/O 바운드 서버는 코어 수 × 2~4 가 sweet spot 이고, 수만 연결이 되면 스레드 풀을 포기하고 epoll 로 넘어가야 합니다.

## 요점

락은 동시성의 비용이자 정확성의 보증입니다. 큐에는 세마포어, 커넥션 풀에는 mutex + condvar, 캐시에는 RWLock, 단일 카운터에는 atomic — 자원의 접근 패턴에 맞는 프리미티브를 배치하는 것이 설계의 전부입니다.
