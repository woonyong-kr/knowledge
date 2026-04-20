---
title: 네트워크 통신을 CPU·메모리·커널·핸들 네 렌즈로 보기
category: 네트워크
keyword: IO Bridge와 NIC
created: 2026-04-20
updated: 2026-04-20
tags: [cpu, memory, kernel, fd, dma, napi, epoll, numa]
summary: 한 번의 네트워크 통신을 CPU·메모리·커널·파일 핸들 네 렌즈로 나눠 살피고, 송신과 수신을 대칭으로 풀어 성능에 영향을 주는 지점을 정리합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q09-network-cpu-kernel-handle.md
---

## 네 개의 렌즈

같은 한 번의 통신을 네 렌즈로 보면 각각 다른 장면이 드러납니다.

CPU 관점은 제어와 복사입니다. 데이터 이동은 DMA 가 대신 하지만, 유저 ↔ 커널 복사, 체크섬 계산, TCP 상태 관리(seq·ack, 혼잡제어 업데이트), syscall 진입·복귀, 인터럽트 처리는 CPU 가 사이클을 씁니다. 캐시 hit/miss, 브랜치 예측이 그대로 네트워크 성능에 반영됩니다.

메모리 관점은 데이터가 DRAM 의 여러 위치를 오가는 그림입니다. 유저 버퍼 → 커널 소켓 버퍼(`sk_buff`) → NIC DMA 버퍼 링 → NIC 내부 FIFO 로 흐르고, 각 구간이 메모리 대역폭을 소모하고 물리 페이지를 붙잡습니다. `sk_buff` 는 slab allocator 가 관리합니다.

커널 관점은 서브시스템 함수 체인입니다. socket 계층(BSD API) → `proto_ops`(TCP·UDP) → IP 계층 → qdisc(큐잉) → 드라이버 순서로 함수가 돕니다. softirq, NAPI, tasklet 이라는 비-프로세스 컨텍스트도 관여합니다.

핸들(fd) 관점은 정수 한 개가 여는 체인입니다. 유저는 `int sockfd` 하나만 보지만, 이 정수가 `fdtable[sockfd] → struct file → struct socket → struct sock` 체인을 엽니다. 파일과 똑같이 `read`·`write`·`close` 로 다룰 수 있는 이유가 여기에 있습니다.

## 송신과 수신의 대칭

송신(write) 경로입니다.

```text
CPU       : write(3, buf, 95)  -> syscall 트랩 (~100ns)
핸들      : fd=3 -> file -> socket -> tcp_sock
메모리    : copy_from_user: 유저 buf(95B) -> sk_buff
커널      : tcp_sendmsg -> tcp_write_xmit -> ip_output -> dev_queue_xmit
CPU       : TCP 헤더 적기, 체크섬 계산, IP 헤더 적기
핸들      : qdisc -> driver->ndo_start_xmit(skb)
메모리    : NIC TX descriptor 에 sk_buff 물리주소 기록
CPU       : MMIO doorbell 쓰기
NIC       : DMA 로 DRAM -> NIC 프레임 버퍼 (CPU 개입 없음)
NIC PHY   : 선로에 전기·광 신호 송출
NIC->CPU  : TX 완료 IRQ -> 드라이버가 sk_buff 반환
```

수신(read) 경로입니다.

```text
NIC PHY   : 프레임 수신
NIC       : DMA 로 NIC -> DRAM 의 RX 링 버퍼 (CPU 개입 없음)
NIC->CPU  : RX IRQ (또는 NAPI polling 스케줄)
CPU/커널  : softirq NET_RX 에서 sk_buff 를 꺼냄
커널      : __netif_receive_skb -> ip_rcv -> tcp_v4_rcv
CPU       : 체크섬 검증, seq 검사, reordering 큐 처리
핸들      : 4-tuple 로 소켓 검색 -> sock->sk_receive_queue 에 enqueue
커널      : read() 로 대기중인 프로세스가 있으면 wake up
CPU       : read 진입 후 copy_to_user: sk_buff -> 유저 buf
메모리    : DRAM R(sk_buff) -> DRAM W(유저 buf) == 복사 1회
CPU       : 리턴, 유저 프로세스 재개
```

대칭이지만 수신은 "인터럽트 → softirq → 유저" 3 단계가 있어 레이턴시가 더 긴 경향이 있습니다.

## 성능에 영향을 주는 요소

관점별로 정리하면 다음과 같습니다.

- CPU: 시스템콜 횟수, 복사 횟수, 체크섬(NIC offload 유무), 인터럽트 coalescing. 많은 연결은 많은 컨텍스트 스위치로 이어집니다.
- 메모리: `sk_buff` 할당·해제 빈도(slab 단편화), NUMA 배치(CPU·NIC 의 거리), 캐시 정렬, TCP 송·수신 버퍼 크기(`tcp_rmem`, `tcp_wmem`).
- 커널: qdisc 정책(fq_codel 등), backpressure, `SO_REUSEPORT` 로 소켓 분산, epoll·kqueue·io_uring 선택, net namespace 비용.
- 핸들: 열린 fd 개수(per-process limit), `select` 는 O(N) 이지만 epoll 은 O(1) 에 가까움, `accept4()` 로 `SOCK_NONBLOCK`·`SOCK_CLOEXEC` 원샷 설정.

예를 들어 `perf top` 에서 `copy_user_enhanced_fast_string` 이 뜨면 메모리·CPU 복사 문제이고, `__netif_receive_skb` 가 높으면 커널 스택, `epoll_wait` 에서 블록이 잦으면 핸들·이벤트 루프 문제입니다.

한 줄로 정리하면 네트워크 I·O 는 "fd 로 커널에 일을 시키고, CPU 가 복사와 제어를 하며, 메모리에서 sk_buff 가 흘러가고, 커널 함수 체인이 NIC 까지 밀어준다" 는 네 문장의 합입니다.
