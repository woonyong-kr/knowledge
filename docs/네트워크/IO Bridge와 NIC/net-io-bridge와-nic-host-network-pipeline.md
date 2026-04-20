---
title: 호스트 내부 송신 파이프라인 — write 부터 이더넷 선로까지
category: 네트워크
keyword: IO Bridge와 NIC
created: 2026-04-20
updated: 2026-04-20
tags: [pipeline, sk_buff, dma, nic, tcp, ethernet, hop-by-hop]
summary: 프로세스가 `write(sockfd, buf, n)` 을 호출한 순간부터 이더넷 선로로 비트가 나가기까지 유저 버퍼·커널 스택·NIC 의 각 단계에서 벌어지는 일을 수치 예제로 추적합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q08-host-network-pipeline.md
---

## 한 번의 write 가 거치는 파이프라인

한 문장으로 쓰면 "유저 버퍼 → 커널 소켓 버퍼 → TCP·IP 처리(헤더 붙이기) → NIC 드라이버 → NIC → 이더넷" 입니다. 각 단계마다 데이터가 복사되고, 헤더가 덧붙고, DMA 로 카드에 전달됩니다.

```text
유저 공간                         커널 공간                              하드웨어
────────────                      ─────────────                         ────────────
process
  │   write(sockfd, buf, n)
  │   ── system call ─────────>   트랩, 커널 모드 진입
  │
  │                               VFS / sockfs
  │                                 ㄴ fd 테이블에서 struct socket 찾기
  │
  │                               socket layer
  │                                 ㄴ sendmsg() 호출
  │                                 ㄴ 유저 buf 를 커널 소켓 송신 버퍼
  │                                    (sk_buff 체인) 로 복사
  │
  │                               TCP layer
  │                                 ㄴ MSS 기준으로 segment 쪼개기
  │                                 ㄴ seq·ack·flags·포트 적은 TCP 헤더
  │                                 ㄴ 체크섬 계산
  │
  │                               IP layer
  │                                 ㄴ 라우팅 테이블 보고 next-hop 결정
  │                                 ㄴ src·dst IP, TTL, proto 적은 IP 헤더
  │                                 ㄴ 필요 시 fragmentation
  │
  │                               ARP + Ethernet layer
  │                                 ㄴ next-hop MAC 조회 (ARP cache)
  │                                 ㄴ dst MAC · src MAC · EtherType
  │
  │                               Driver (NIC driver)
  │                                 ㄴ sk_buff → TX ring descriptor 기록
  │                                 ㄴ NIC 에 "보내라" MMIO doorbell
  │
  │                                                          NIC (HW)
  │                                                            ㄴ DMA 로 DRAM 프레임 읽음
  │                                                            ㄴ MAC 회로: 프리앰블 + 프레임 + CRC 송출
  │                                                            ㄴ TX 완료 IRQ
  │
  <── 확인 (write 는 커널 버퍼에 복사되면 리턴)
```

중요한 포인트 네 가지입니다.

첫째, `write` 가 리턴한 순간이 "선로에 비트가 나갔다" 는 뜻은 아닙니다. 리턴은 커널 소켓 버퍼에 복사가 끝난 시점이고, 실제 전송은 TCP 혼잡 제어와 NIC 스케줄에 달려 있습니다.

둘째, 유저 → 커널 복사(`copy_from_user`) 는 반드시 한 번 일어납니다. 제로카피 최적화(`sendfile`, `splice`, `MSG_ZEROCOPY`) 는 이 복사를 없애거나 커널 내부 복사로 대체하는 기법입니다.

셋째, NIC 에 데이터가 넘어가는 방법은 CPU 가 바이트를 하나씩 넣는 것이 아니라 DMA 입니다. 드라이버가 descriptor 에 "물리 주소 X 에서 N 바이트 읽어 송신하라" 고 써두면 NIC 가 스스로 DRAM 을 읽어 갑니다. CPU ↔ 메모리 ↔ PCIe NIC 를 잇는 I·O 브리지(PCH, PCIe Root Complex) 가 이 DMA 경로를 제공합니다.

넷째, 이더넷 계층은 항상 "다음 홉" 까지의 프레임을 만듭니다. 최종 목적지 IP 가 다른 서브넷이면 목적지 MAC 은 최종 호스트 MAC 이 아니라 게이트웨이 라우터의 MAC 입니다.

## 수치로 보는 프레임 생성

CSAPP 워크스루와 동일한 시나리오로 수치를 넣어 봅니다.

- 클라이언트 A: `128.2.194.242`, MAC `AA:AA:AA:AA:AA:AA`, 임시 포트 `51213`
- 게이트웨이 R 의 A 쪽 MAC: `11:11:11:11:11:11`
- 서버 B: `208.216.181.15`, MAC `BB:BB:BB:BB:BB:BB`, 포트 `80`
- 유저 페이로드: `GET /home.html HTTP/1.0\r\nHost: www.example.net\r\n...\r\n\r\n` → 95B

호스트 A 내부의 일을 단계별 수치로 쓰면 다음과 같습니다.

```text
[1] write(sockfd, buf95B, 95)           -> syscall 트랩

[2] 소켓 버퍼로 복사
    커널 소켓 송신 버퍼(예: 87,380B, tcp_wmem 중간값) 에 95B 복사

[3] TCP 세그먼트화
    MSS = 1460B 이므로 95B 는 한 세그먼트
    TCP 헤더 20B 붙임
      src port = 51213 (0xC82D)
      dst port = 80    (0x0050)
      seq, ack, flags(PSH|ACK), window, checksum
    -> 95 + 20 = 115B

[4] IP 패킷화
    IP 헤더 20B 붙임
      version=4, IHL=5, TTL=64
      proto=6 (TCP)
      src IP = 128.2.194.242
      dst IP = 208.216.181.15
      total-length = 115 + 20 = 135B
    -> 115 + 20 = 135B

[5] 이더넷 프레임화
    라우팅 결과: dst IP 가 같은 서브넷이 아님 -> next-hop = 라우터 R
    ARP 캐시에서 R 의 MAC 조회 -> 11:11:11:11:11:11
    Ethernet 헤더 14B
      dst MAC = 11:11:11:11:11:11   (라우터 R, 최종 서버가 아님!)
      src MAC = AA:AA:AA:AA:AA:AA
      EtherType = 0x0800
    프레임 = 14 + 135 = 149B
    (+ FCS 4B 는 NIC 가 자동 부착 -> 실제 선로엔 153B)

[6] NIC 드라이버
    sk_buff 의 물리 주소를 TX descriptor 에 기록
    MMIO 로 doorbell 레지스터에 값 쓰기

[7] NIC (HW)
    DMA 로 149B 를 DRAM -> NIC 로 가져옴
    프리앰블 + 프레임 + FCS 를 Ethernet PHY 로 송출
    TX 완료 IRQ -> 드라이버가 sk_buff 반환
```

라우터 R 을 지날 때의 변화는 다음과 같습니다.

```text
IP 헤더:      src=128.2.194.242, dst=208.216.181.15    (유지)
TTL:          64 -> 63                                   (1 감소)
Ethernet:     src MAC, dst MAC 모두 교체
              ㄴ src MAC = R 의 LAN2 쪽 MAC (22:22:22:22:22:22)
              ㄴ dst MAC = 서버 B (BB:BB:BB:BB:BB:BB)
```

"IP 는 끝점이 바뀌지 않고, MAC 은 홉마다 바뀐다" 는 규칙이 실제로 이렇게 구현됩니다.

## 라우터 MAC 이 바뀌는 이유

처음 보면 "방금 들어올 땐 라우터 MAC 이 `11:11:..` 였는데, 나갈 땐 왜 `22:22:..` 로 달라지나" 가 헷갈립니다. 핵심은 한 가지입니다. 라우터는 MAC 주소가 1개가 아니라 꽂혀 있는 인터페이스(포트) 마다 1개씩을 가집니다.

```text
                 라우터 R
        ┌──────────────────────────┐
  LAN1  │ [eth0: 11:11:11:11:11:11]│  LAN2
 ───────┤                          ├────────
        │ [eth1: 22:22:22:22:22:22]│
        │       IP 라우팅 테이블    │
        └──────────────────────────┘
```

프레임이 라우터를 통과할 때 벌어지는 일을 풀어 쓰면 이렇습니다.

```text
[클라이언트 A 에서 출발]
 프레임 ①
   dst MAC = 11:11:11:11:11:11  (라우터 R 의 eth0)
   src MAC = AA:AA:AA:AA:AA:AA
   IP src/dst = A -> B, TTL = 64
        │
        v LAN1 선로
[라우터 R 의 eth0 수신]
  NIC(eth0): "dst MAC 이 내거(11:11..) -> 수신"
  IP 계층  : "IP dst 가 내 IP 아님 -> 포워딩"
             라우팅 테이블: B 는 LAN2 방향
             ARP 캐시   : B 의 MAC = BB:BB:..
  프레임 재작성:
    IP: src/dst IP 유지, TTL 64 -> 63, Header Checksum 재계산
    Ethernet(새로 만듦):
      src MAC = 22:22:22:22:22:22  <- eth1 의 MAC
      dst MAC = BB:BB:BB:BB:BB:BB  <- 서버 B
        │
        v eth1 로 LAN2 송출
[서버 B 수신]
 프레임 ②
   dst MAC = BB:BB:BB:BB:BB:BB
   src MAC = 22:22:22:22:22:22
   IP src/dst = A -> B (그대로)
```

이더넷(MAC) 은 같은 LAN 안의 한 구간만 담당하는 주소입니다. 서로 다른 LAN 은 MAC 만으로는 도달할 수 없고, 스위치는 자기 LAN 에 붙은 MAC 만 기억하기 때문에 다른 LAN 의 MAC 은 알 수가 없습니다.

```text
구간                   바뀌나?         이유
--------------------------------------------------------
IP src/dst             안 바뀜        "누가 누구에게" 논리 주소 (end-to-end)
MAC src/dst            매 홉마다 교체  "현재 구간의 두 이웃" 물리 주소 (hop-by-hop)
TTL                    매 홉마다 -1   루프 방지
IP Header Checksum     매 홉마다 재계산 TTL 이 바뀌므로
TCP Checksum           안 바뀜        end-to-end 무결성
```

`11:11:..` 은 R 의 LAN1 쪽 포트(eth0) MAC 이고, 이 포트는 LAN1 케이블에만 물려 있어 LAN2 위에는 물리적으로 존재하지 않습니다. R 이 LAN2 로 프레임을 내보낼 때는 LAN2 에 꽂힌 포트(eth1) 의 MAC, 즉 `22:22:..` 을 src MAC 으로 써야 LAN2 위의 스위치·서버가 그 프레임을 인식합니다.

## 프로토콜 소프트웨어는 어디 있는가

대부분은 커널 안에 있습니다. Linux 기준으로 TCP·IP 스택은 커널 서브시스템(`net/ipv4/`, `net/core/`, `drivers/net/`) 입니다. 유저 프로세스는 소켓 파일 디스크립터를 통해 이 서브시스템에 일을 시킬 뿐, 프로토콜 자체를 돌리지 않습니다.

- 유저 프로세스: 브라우저, Tiny 서버, 클라이언트. HTTP 메시지를 만들고 `write` 를 호출합니다.
- 커널 스레드·softirq·NAPI: TCP 재전송, 혼잡 제어, ACK 생성, 체크섬 검증을 실제로 수행하는 주체입니다. 유저 공간에 보이지 않지만 프로세스·스레드라는 점에서는 맞는 표현입니다.
- 유저 공간 스택: DPDK, QUIC(HTTP/3) 일부, user-space TCP 같은 구현체는 유저 프로세스 안에서 돕니다. 고성능이 필요할 때 쓰입니다.

CSAPP 관점으로는 "TCP·IP = 커널 서브시스템, 애플리케이션은 소켓으로만 접근" 이 정답이고, 그 위에서 사용자가 만드는 프로그램(Tiny, 프록시) 이 유저 프로세스입니다. 소켓 함수가 시스템콜이라는 문장이 여기서 성립합니다.
