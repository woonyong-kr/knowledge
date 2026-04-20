---
title: 스레드 풀과 Async I/O — 동시성 서버의 세 가지 전략
category: 네트워크
keyword: Concurrent Server
created: 2026-04-20
updated: 2026-04-20
tags: [thread-pool, epoll, io-uring, reactor, futex, concurrent-server, blocking-io]
summary: iterative 서버에서 스레드 풀 · epoll 이벤트 루프 · io_uring 까지의 진화를 CPU·메모리·커널·핸들·시스템콜 다섯 관점으로 비교합니다. "커널에 block 을 위임하느냐, 유저가 상태 기계로 관리하느냐" 가 선택의 핵심입니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q16-thread-pool-async.md
---

# 스레드 풀과 Async I/O — 동시성 서버의 세 가지 전략

iterative 서버는 한 번에 한 클라이언트만 처리하므로 실전 서비스에서는 곧 한계를 만납니다. 동시성 서버는 크게 세 가지 구현 전략 중 하나를 고르게 됩니다.

## 세 가지 동시성 전략

- 요청마다 프로세스·스레드 생성 (per-request) — 단순하지만 생성 비용이 큽니다.
- 스레드 풀 (thread pool) — 워커 N 개를 미리 만들어 두고 작업 큐에서 꺼내 처리합니다.
- 이벤트 루프 + 소수 스레드 (reactor) — 한 스레드가 epoll 로 수천 개 소켓을 지켜보며 준비된 것만 처리합니다.

SQL API 서버·Proxy Lab 2단계처럼 소규모 학습 서비스에서는 두 번째(전통적 스레드 풀) 가 기본입니다.

## 스레드 풀의 구조

```text
                   job queue
                   [fd=4  fd=5  fd=6  fd=7  fd=8]
                      |
  main thread         |        worker threads (N 개)
  -----------         |        --------------------
  listenfd = open_listenfd(port)
  while (1) {
      connfd = accept(listenfd, ...);   -- enqueue -->  (condvar wait) -- dequeue -->
      sbuf_insert(&sbuf, connfd);                       doit(connfd)
  }                                                     close(connfd)
```

- mutex 로 큐를 보호하고 condvar 로 "비었을 때 기다리고 채워지면 깨우기" 를 합니다.
- 각 worker 는 독립적으로 `read/write` 를 호출합니다. 하나가 block 되어도 다른 worker 가 일합니다.

장점은 I/O 블로킹을 스레드 개수만큼 병렬화하는 단순성이고, 단점은 연결 수가 스레드 수를 넘으면 대기가 쌓인다는 점입니다. 대규모 서비스는 이 한계를 이벤트 루프로 우회합니다.

## 다섯 관점에서 본 스레드 풀

### CPU

스레드 개수의 상한은 논리 코어 수와 I/O 대기 비율에 좌우됩니다. I/O 바운드일수록 스레드 수 > 코어 수가 유리합니다. 블로킹 read 에서 sleep 하는 동안엔 CPU 를 쓰지 않기 때문입니다. `SO_REUSEPORT` 나 affinity 를 써서 작업 - 스레드 매핑을 고정하면 L1/L2 캐시 친화성이 올라갑니다.

### 메모리

각 스레드는 기본 8MB 의 자기 스택을 갖습니다. 스레드 수 × 8MB 가 기본 오버헤드입니다. 공유 자료구조(캐시·B+Tree·버퍼) 는 여러 스레드가 같은 DRAM 페이지를 접근하므로 false sharing 과 캐시 무효화를 조심해야 합니다. 연결 폭증 시에는 `sk_buff` 의 slab 단편화도 변수입니다.

### 커널

`pthread_create` 는 Linux 에서 `clone(CLONE_VM | CLONE_FS | CLONE_FILES | ...)` 로 내려갑니다. 주소 공간과 파일 테이블을 공유하는 경량 프로세스를 만드는 호출입니다. mutex·condvar 는 대부분 **futex** 기반이어서 경합이 없을 때는 유저 공간에서 atomic 만으로 끝나고, 경합이 있을 때만 커널이 깨웁니다.

### 핸들

`accept()` 가 반환하는 connfd 는 per-process 이므로 모든 스레드가 공유합니다. 덕분에 worker 가 `read(connfd, ...)` 를 그대로 호출할 수 있습니다. close 는 참조 카운트로 관리되므로 worker 가 끝까지 책임집니다. `RLIMIT_NOFILE` 을 넘기면 accept 가 `EMFILE` 로 실패하므로 대규모 서버는 `ulimit -n` 을 올려 둡니다.

### 시스템콜

```text
main:
   accept -> sys_accept4 (listen 큐 -> 새 sk, 새 file, 새 fd)

worker:
   pthread_cond_wait -> futex(FUTEX_WAIT) -> block
   (signal -> futex(FUTEX_WAKE) -> worker 깨어남)
   read  -> sys_read  -> sock_read_iter -> tcp_recvmsg (큐에 없으면 block)
   write -> sys_write -> sock_write_iter -> tcp_sendmsg
   close -> sys_close -> sock_release -> FIN 전송
```

"blocking I/O + 여러 스레드" 전략은 커널에 block 을 위임하는 구조입니다. 간단하지만 스레드 수가 많아지면 스케줄링과 메모리 비용이 붙습니다.

## 스레드 풀 vs epoll reactor

```text
              스레드 풀 (blocking I/O)            epoll reactor (async I/O)
-----------------------------------------------------------------------------
연결 N개       스레드 N개                          스레드 1~few
프로그래밍     read/write 그냥 호출                 event 루프 + fd 상태 관리
블록 동안      커널이 스레드를 sleep                스레드는 "준비된 fd" 만 처리
스케일         수천~만 connections                  수만~수십만 connections
대표 예        전통적 Apache, Tomcat                nginx, Node.js, Netty, Go runtime
구현 시스템콜  read/write/pthread/futex             epoll_create/ctl/wait + NIO
복잡도         코드가 단순                          상태 머신(콜백/async-await) 필요
```

epoll 의 골격은 다음과 같습니다.

```c
int ep = epoll_create1(0);
struct epoll_event ev = { .events = EPOLLIN, .data.fd = listenfd };
epoll_ctl(ep, EPOLL_CTL_ADD, listenfd, &ev);

struct epoll_event events[MAX];
while (1) {
    int n = epoll_wait(ep, events, MAX, -1);    /* block */
    for (int i = 0; i < n; i++) {
        int fd = events[i].data.fd;
        if (fd == listenfd) {
            int connfd = accept4(listenfd, ..., SOCK_NONBLOCK);
            epoll_ctl(ep, EPOLL_CTL_ADD, connfd, &ev_in);
        } else {
            handle_request(fd);                 /* non-blocking read/write */
        }
    }
}
```

`io_uring` 은 여기서 한 단계 더 나아가 시스템콜 자체를 배치로 커널에 맡깁니다. submission/completion 두 링 버퍼에 요청을 쓰면 커널이 알아서 돌리고 결과를 연결해 줍니다. 컨텍스트 스위치가 거의 사라지지만 프로그래밍 모델이 더 복잡합니다.

## 코드 레벨의 선택 기준

- 연결 수가 수천 이하이고 코드 단순성이 우선이면 스레드 풀 + blocking I/O.
- 연결 수가 수만 이상이고 레이턴시에 민감하면 epoll·kqueue reactor 또는 언어 런타임의 async.
- 극한 성능이 필요한 커스텀 인프라에서는 io_uring·DPDK·유저공간 TCP 까지 간다.

결국 동시성의 본질은 "커널에 block 을 위임할지, 유저가 상태 기계로 전부 관리할지" 중 하나를 선택하는 것이고, 이 선택이 CPU·메모리·커널·핸들 비용의 분포를 결정합니다.
