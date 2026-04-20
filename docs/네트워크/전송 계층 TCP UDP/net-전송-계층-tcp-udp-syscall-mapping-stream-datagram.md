---
title: TCP·UDP 와 소켓 시스템콜 매핑 — 스트림과 데이터그램의 차이
category: 네트워크
keyword: 전송 계층 TCP UDP
created: 2026-04-20
updated: 2026-04-20
tags: [tcp, udp, syscall, proto_ops, stream, datagram, host-to-host]
summary: `connect`·`send`·`recvfrom` 같은 소켓 함수가 커널에서 어떻게 TCP·UDP 경로로 디스패치되는지 살펴보고, "host-to-host vs process-to-process" 표현과 두 프로토콜의 공통점·차이점을 정리합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q07-tcp-udp-socket-syscall.md
---

## 소켓 함수가 시스템콜로 동작하는 구조

`socket`, `bind`, `listen`, `accept`, `connect`, `read`, `write`, `recvfrom`, `sendto`, `close` 는 모두 유저 공간에서 호출되면 "glibc 래퍼 → syscall 명령 → 커널 진입 → 커널 내부 구현 실행 → 리턴" 구조로 동작합니다. CSAPP 가 이 함수들을 Unix I·O 의 확장으로 소개하는 것도 같은 맥락입니다.

예를 들어 `connect` 한 번이 어떻게 동작하는지 펼치면 다음과 같습니다.

```text
[ 유저 공간 ]
    connect(sockfd, (SA*)&servaddr, sizeof(servaddr));
        │
        v  glibc 내부 (libc.so) 의 connect 래퍼
             ㄴ 인자 세팅 (rdi, rsi, rdx 레지스터에)
             ㄴ syscall 명령 실행  (x86-64: syscall; 번호 = 42)
        │
        v
[ 커널 진입, ring 3 -> ring 0 ]
        │
        v  syscall_64 entry point
             ㄴ sys_call_table[__NR_connect] 디스패치
             ㄴ __sys_connect()
                  ㄴ sockfd_lookup_light(fd): fd 테이블 -> struct socket
                  ㄴ sock->ops->connect(...)
                        ㄴ TCP 면 tcp_v4_connect()
                             ㄴ 3-way handshake 시작 (SYN 보냄, ACK 대기)
                        ㄴ UDP 면 udp_connect() (주소만 기록, 핸드셰이크 없음)
        │
        v  커널이 완료되면 결과를 rax 에 넣고 sysret
[ 유저 공간으로 복귀 ]
    return 값 -> errno
```

핵심은 세 가지입니다.

첫째, 파일 디스크립터는 정수 핸들일 뿐이고 커널 내부에서는 `struct file → struct socket → struct sock(TCP 또는 UDP)` 로 이어지는 객체입니다. `read`·`write` 가 소켓에서도 동작하는 이유는 `struct file` 의 `file_operations` 에 소켓용 함수 포인터가 박혀 있기 때문입니다.

둘째, 프로토콜별 동작은 함수 포인터 테이블(`proto_ops`) 로 분기됩니다. 같은 `send()` 시스템콜이라도 TCP 소켓이면 `tcp_sendmsg`, UDP 소켓이면 `udp_sendmsg` 로 갑니다. 이것이 "소켓은 프로토콜 독립적인 범용 인터페이스" 라는 표현의 실제 구현입니다.

셋째, 시스템콜은 컨텍스트 스위치 비용이 크기 때문에 네트워크 성능이 문제가 되면 `sendfile`, `splice`, `io_uring`, 유저 공간 TCP 등으로 이 비용을 줄이는 방향으로 최적화가 들어갑니다.

## host-to-host 와 process-to-process 의 의미

CSAPP 키워드 트리에 그대로 쓰여 있는 이 문구는 축약 표현이라 오해하기 쉽습니다. 책이 세 계층을 보는 시선은 다음과 같습니다.

```text
IP   : host-to-host    (호스트 → 호스트까지 비신뢰 배달)
UDP  : process-to-process (IP 위에 "포트 → 프로세스" 디먹싱만 더함, 여전히 비신뢰)
TCP  : process-to-process, 신뢰성 있는 full-duplex connection
```

책에서 "TCP 는 host-to-host" 로 읽혔다면 비교의 강조점이 다르기 때문입니다. TCP 가 해 주는 일의 핵심이 "두 호스트 사이에 신뢰성 있는 바이트 스트림 연결을 만드는 것" 이어서 "host-to-host connection" 이라는 이미지로 표현한 것이고, UDP 는 연결 개념이 없어 "포트로 프로세스를 찾아 데이터그램 하나를 던진다" 는 의미로 "process-to-process" 를 강조한 것입니다.

정확한 이해는 다음과 같습니다.

- IP 는 "호스트(IP 주소) → 호스트" 까지만 책임집니다. 어느 프로세스에게 줄지는 모릅니다.
- UDP·TCP 는 IP 위에 "포트 번호" 라는 다중화 키를 얹어 프로세스를 구분합니다. 둘 다 엄밀히 말하면 process-to-process 입니다.
- 차이는 "연결과 신뢰성" 에 있습니다.

CSAPP 문구는 "TCP 는 연결을 중심에 둔다(host-to-host connection 의 이미지), UDP 는 연결 없이 포트로 던진다(process-to-process messaging 의 이미지)" 정도로 읽는 것이 낫습니다.

## TCP 와 UDP 의 공통점·차이

공통점은 다음과 같습니다.

- 둘 다 IP 위에서 동작합니다. IP 헤더 다음에 각자의 헤더가 붙습니다.
- 둘 다 포트 번호로 프로세스를 구분합니다.
- 둘 다 유저 입장에서는 소켓 인터페이스(`socket`·`read`·`write`·`recvfrom`·`sendto`) 로 다룹니다.
- 둘 다 체크섬을 계산합니다.

차이점은 다음과 같습니다.

```text
                 TCP                         UDP
-------------------------------------------------------------
연결            3-way handshake 로 수립        없음 (연결리스 datagram)
신뢰성          seq·ack, 재전송, 순서 보장      없음 (loss, 순서 섞임 허용)
흐름 제어        window 기반                    없음
혼잡 제어        cwnd, slow start 등            없음
전송 단위        byte stream (경계 없음)         datagram (메시지 경계 보존)
헤더 크기        20B 이상                       8B
API              socket·connect·listen·accept   socket·sendto·recvfrom
                 read·write                     연결형으로도 가능하나 보통 비연결형
사용 예          HTTP, SSH, TLS, DB 커넥션      DNS(기본), VoIP, 게임 실시간, QUIC 하부
```

두 프로토콜을 고르는 기준을 한 줄로 적으면 "손실돼도 되니 빠르게" = UDP, "느려도 되니 정확하게 순서대로" = TCP 입니다. 네트워크 프로그래밍에서 가장 큰 결정 지점입니다.
