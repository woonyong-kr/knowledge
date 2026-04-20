---
title: 소켓의 물리·소프트웨어 동작 원리 — fd 한 개가 여는 커널 체인
category: 네트워크
keyword: 소켓 시스템콜
created: 2026-04-20
updated: 2026-04-20
tags: [socket, sockfd, sk_buff, nic, dma, io-bridge, kernel]
summary: 소켓이 하드웨어의 구멍이 아니라 소프트웨어 객체임을 밝히고, `sockfd` 한 개가 커널 안에서 어떤 자료구조 체인을 여는지, 또 데이터가 CPU·DRAM·NIC 를 어떻게 오가는지 설명합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q05-socket-principle.md
---

## 소켓은 소프트웨어 객체입니다

소켓은 "하드웨어에 있는 구멍" 이 아니라 소프트웨어 객체입니다. 물리적인 것은 NIC(Network Interface Card) 뿐이고, 소켓은 그 위에 OS 커널이 만들어 놓은 논리적 엔드포인트입니다. 이해를 돕는 비유는 "파일" 입니다. 파일이 물리적으로는 디스크 블록이지만 유저에게는 `int fd` 로 보이듯, 소켓도 물리적으로는 NIC·DRAM 의 버퍼인데 유저에게는 `int sockfd` 로 보입니다.

Linux 기준으로 `sockfd` 한 개가 여는 객체 체인은 다음과 같습니다.

```text
유저 공간
    sockfd (int)
        │
        v
[ per-process fd 테이블 ]
    task_struct -> files_struct -> fdtable[fd] = struct file*
        │
        v
struct file
    f_op = socket_file_ops              <- read·write 가 소켓용으로 붙음
    private_data = struct socket*
        │
        v
struct socket                          <- BSD 소켓 레벨 (범용)
    type = SOCK_STREAM | SOCK_DGRAM ...
    ops  = inet_stream_ops             <- 함수 포인터 테이블
    sk   = struct sock*
        │
        v
struct sock (또는 tcp_sock, udp_sock)  <- 프로토콜별 상태
    sk_receive_queue   : 수신 sk_buff 체인 (수신 버퍼)
    sk_write_queue     : 송신 대기 sk_buff 체인 (송신 버퍼)
    sk_state           : TCP 상태 (ESTABLISHED, TIME_WAIT ...)
    tcp_sock:
       snd_nxt, rcv_nxt, rtt_est, cwnd, rwnd ...
```

소켓의 물리적 재료는 두 가지입니다.

- `sk_buff` : 한 패킷을 감싸는 커널 자료구조. 실제 바이트는 DRAM 페이지에 있고, `sk_buff` 는 그걸 가리키는 메타데이터·포인터 집합입니다.
- NIC : 물리 회로. TX·RX ring(descriptor 큐) 을 가지고 있어 커널이 `sk_buff` 를 descriptor 로 연결해 주면 DMA 로 가져갑니다.

그래서 "소켓이 물리적으로 어떻게 되어 있느냐" 의 답은 "DRAM 안의 `sk_buff` 큐 + NIC ring buffer + 둘을 이어 주는 DMA 경로" 입니다.

## CPU · DRAM · NIC 가 만나는 경로

I/O Bridge(PCH, IOH 칩셋) 를 중심으로 본 구조입니다.

```text
[ CPU ]──── system bus ────┐
                            │
                     ┌──────┴──────┐
                     │  IO Bridge  │  (memory controller hub + PCIe root complex)
                     └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              v             v             v
           DRAM         PCIe 링크         ...
                            │
                            v
                      [ NIC (PCIe 카드) ]
                          │
                          └── Ethernet PHY ── RJ-45 ── 케이블
```

송신 경로는 아래 순서입니다.

```text
1) CPU 가 write() 로 유저 버퍼(buf) 를 sk_buff 에 copy_from_user
     ㄴ CPU·DRAM 사이의 버스(시스템 버스 + memory controller) 사용
2) TCP·IP 처리 후 sk_buff 를 NIC 의 TX descriptor 에 등록
     ㄴ 드라이버가 MMIO 로 NIC 레지스터에 doorbell 기록
3) NIC 가 DMA 로 DRAM 에서 프레임 바이트를 직접 읽음
     ㄴ CPU 개입 없이 IO Bridge ↔ DRAM ↔ NIC 전송
     ㄴ 끝나면 NIC 가 IRQ 를 발생시켜 CPU 를 깨움
4) NIC MAC 블록이 프리앰블 + 프레임 + CRC 를 PHY 로 송신
```

수신 경로는 거의 대칭입니다.

```text
1) Ethernet PHY -> NIC MAC 수신 -> DMA 로 DRAM 의 RX 버퍼에 기록
2) NIC 가 IRQ (또는 NAPI polling) 로 커널을 깨움
3) softirq 에서 프로토콜 스택이 sk_buff 를 TCP·UDP 소켓 수신 큐로 넣음
4) read() 를 호출한 프로세스가 깨어나고 copy_to_user 로 유저 버퍼에 복사
```

세 가지 관찰 포인트가 있습니다.

- CPU 는 많은 경우 데이터를 손으로 만지지 않습니다. DMA 가 대신 합니다. CPU 가 하는 일은 주로 "어디에서 어디로 얼마를" 이라는 메타데이터 설정입니다.
- 유저 ↔ 커널 복사는 반드시 CPU 가 합니다. 그래서 고성능 서버는 이 복사를 줄이려고 `sendfile`, `splice`, `MSG_ZEROCOPY`, `io_uring` 같은 기법을 씁니다.
- I/O Bridge 는 메모리 대역폭과 PCIe 대역폭을 모두 중재합니다. 네트워크 트래픽이 늘면 DRAM 대역폭 경합이 CPU 성능에도 영향을 줍니다.

## sockfd 한 개가 여는 커널 동작

```c
int sockfd = socket(AF_INET, SOCK_STREAM, 0);    // 예: sockfd = 3
```

커널이 하는 일입니다.

```text
1) alloc_inode -> alloc_file -> fd_install(fd=3, file)
2) sock = sock_alloc()                <- struct socket
3) sock->ops = &inet_stream_ops
4) sk = sk_alloc(...)                 <- struct sock (TCP 이면 tcp_sock)
5) file->private_data = sock
6) current->files->fdtable->fd[3] = file
```

이후 유저가 `write(3, buf, n)` 을 부르면 다음 체인이 돕니다.

```text
fdget(3) -> struct file*
 -> file->f_op->write_iter
     -> sock_write_iter
         -> sock_sendmsg
             -> sock->ops->sendmsg        (= tcp_sendmsg)
                 -> sk_stream_alloc_skb
                 -> skb_copy_to_kernel (copy_from_user)
                 -> tcp_push_one / tcp_write_xmit
                     -> ip_output -> ip_finish_output
                         -> dev_queue_xmit
                             -> driver->ndo_start_xmit
                                 -> NIC TX ring 에 등록, doorbell
```

"소켓 하나" 라는 것은 사실 위 전체 체인이 합쳐진 그림이고, `sockfd` 는 그 모든 것에 들어가는 핸들 역할만 합니다. 파일 디스크립터와 같은 원리이므로 CSAPP 가 10장 I·O 뒤에 11장 네트워크를 바로 붙인 것입니다.
