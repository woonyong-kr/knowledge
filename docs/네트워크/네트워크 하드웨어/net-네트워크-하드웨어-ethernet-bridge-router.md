---
title: 네트워크 하드웨어 — Ethernet Bridge Router 와 프레임의 구조
category: 네트워크
keyword: 네트워크 하드웨어
created: 2026-04-20
updated: 2026-04-20
tags: [ethernet, bridge, router, mac, lan, wan, frame, csapp]
summary: 이더넷 세그먼트, 브릿지, 라우터, LAN·WAN 의 개념 차이와 한 이더넷 프레임이 실제로 어떤 필드로 구성되는지 바이트 단위로 풀어봅니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q01-network-hardware.md
---

## 이더넷·브릿지·라우터는 무엇이 다른가

세 장치는 "대역폭만 다른 같은 것"이 아닙니다. 연결의 범위와 연결 단위가 각각 다릅니다.

이더넷 세그먼트는 가장 기본 단위입니다. 여러 호스트가 허브에 꽂혀 있고, 허브는 한 포트에서 들어온 비트를 다른 모든 포트로 그대로 복사합니다. 허브에는 판단력이 없어서 한 호스트가 말하면 같은 세그먼트의 모든 호스트가 동시에 듣습니다. 이 구간에서 프레임을 구분하는 단위가 48비트 MAC 주소입니다.

브릿지는 여러 이더넷 세그먼트를 묶어 더 큰 하나의 LAN 으로 만드는 장치입니다. 포트 뒤에 어떤 MAC 이 사는지 테이블로 기억해, A→B 로 가는 프레임을 B 가 있는 포트로만 전달합니다. 세그먼트끼리 트래픽 간섭이 줄어 전체 대역폭이 허브보다 커집니다. 하지만 브릿지로 묶인 결과물은 여전히 하나의 링크 계층 네트워크이며, 같은 IP 서브넷·같은 브로드캐스트 도메인에 속합니다.

라우터부터 계층이 바뀝니다. 서로 다른 LAN·WAN 을 이어 주는 장치이며, MAC(L2) 이 아니라 IP(L3) 수준에서 판단합니다. 들어온 프레임의 IP 헤더를 보고 라우팅 테이블로 다음 홉을 찾아 내보냅니다. 이때 IP 주소는 그대로이지만 MAC 주소는 홉마다 새로 바뀝니다.

```text
Ethernet segment   (허브 하나, 물리적으로 같은 선)
   │
   v  여러 세그먼트 묶음
Bridged Ethernet   (= LAN, 같은 IP 서브넷)
   │
   v  서로 다른 LAN WAN 묶음
Internet           (= LAN + WAN + Router, IP 로 이어진 이기종 네트워크)
```

## LAN 과 WAN 의 차이

LAN(Local Area Network) 은 건물·캠퍼스 정도 범위를 한 조직이 관리하는 네트워크입니다. 동일한 링크 계층 기술(Ethernet, Wi-Fi) 로 묶여 있고 내부 호스트가 같은 IP 서브넷을 공유합니다.

WAN(Wide Area Network) 은 도시·국가·대륙 단위로 펼쳐진 네트워크입니다. 여러 사업자 장비가 얽혀 있고 링크 계층이 제각각(광, 위성, 셀룰러) 입니다. WAN 은 주로 여러 LAN 을 라우터로 이어 줍니다.

차이는 "어떤 장비냐" 가 아니라 "범위와 운영 주체" 입니다. 공통점은 둘 다 IP 기반이라는 점이며, 인터넷은 LAN 과 WAN 을 라우터로 계속 붙여 만든 네트워크입니다.

## 비트 뭉치는 어떻게 생겼는가

한 번에 나가는 단위가 프레임입니다. 각 계층이 자기 헤더를 앞에 붙이고 맨 뒤에 페이로드를 놓습니다. 수신자는 각 계층 헤더의 주소·길이·타입을 보고 자기 데이터인지 판단합니다.

예시로 작은 HTTP 요청 하나가 담긴 이더넷 프레임을 풀어 보면 다음과 같습니다.

```text
[ 프레임 전체 (Ethernet frame) ≈ 71B 예시 ]

┌──────────────────────── Ethernet Header (14B) ─────────────────────┐
│ 목적지 MAC 6B  │ 출발지 MAC 6B  │ EtherType 2B (0x0800 = IPv4)     │
└────────────────────────────────────────────────────────────────────┘
┌──────────────────────── IP Header (20B) ───────────────────────────┐
│ version/len │ total-length │ TTL │ proto=6(TCP) │ src IP │ dst IP │
└────────────────────────────────────────────────────────────────────┘
┌──────────────────────── TCP Header (20B) ──────────────────────────┐
│ src port │ dst port │ seq │ ack │ flags │ window │ checksum │ urg │
└────────────────────────────────────────────────────────────────────┘
┌──────────────────────── Payload (N B) ─────────────────────────────┐
│  "GET /home.html HTTP/1.0\r\n..."                                  │
└────────────────────────────────────────────────────────────────────┘
                                       + Ethernet FCS 4B (CRC)
```

### Ethernet Header 14B

```
오프셋   0             6            12   14
        ┌─────────────┬─────────────┬────┐
        │ Dst MAC 6B  │ Src MAC 6B  │Type│
        └─────────────┴─────────────┴────┘
```

MAC 주소 48비트는 16진수 2자리씩 `:` 로 끊어 표기합니다. 앞 3바이트(OUI) 는 IEEE 가 제조사에 할당하고, 뒤 3바이트는 제조사가 NIC 마다 부여합니다. 첫 바이트의 최하위 비트는 Unicast(0) / Multicast(1), 그 다음 비트는 Globally unique(0) / Locally administered(1) 을 나타냅니다.

| 특수 MAC 주소 | 용도 |
| --- | --- |
| `FF:FF:FF:FF:FF:FF` | Broadcast |
| `01:00:5E:xx:xx:xx` | IPv4 Multicast |
| `33:33:xx:xx:xx:xx` | IPv6 Multicast |
| `01:80:C2:xx:xx:xx` | Bridge·Switch 제어 (STP) |

EtherType 2바이트는 상위 계층을 식별합니다. `0x0800`=IPv4, `0x86DD`=IPv6, `0x0806`=ARP, `0x8100`=VLAN Tag, `0x8847`=MPLS, `0x88CC`=LLDP 입니다.

### IP Header 20B (RFC 791)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Ver|IHL|   TOS   |         Total Length                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Identification          |Flags|   Fragment Offset       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|      TTL      |   Protocol    |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

IHL 은 헤더 길이를 4바이트 단위로 표현합니다. 옵션이 없으면 `5` 이고 합쳐 첫 바이트는 `0x45` 가 됩니다. TTL 은 라우터를 지날 때마다 1 씩 감소해 0 이 되면 drop + ICMP 에러를 냅니다. Linux 초기값은 64, Windows 는 128 입니다. Protocol 은 상위 계층 식별자로 1=ICMP, 6=TCP, 17=UDP, 41=IPv6-in-IPv4, 47=GRE, 50=ESP, 89=OSPF 입니다. Header Checksum 은 IP 헤더만 대상으로 하며 TTL 이 홉마다 바뀌므로 라우터가 매번 재계산합니다.

### TCP Header 20B (RFC 793)

| 오프셋 | 크기 | 필드 | 의미 |
| --- | --- | --- | --- |
| 0 | 2B | Source Port | 송신 프로세스 포트. 클라이언트는 보통 ephemeral 32768~60999 |
| 2 | 2B | Destination Port | 수신 프로세스 포트 |
| 4 | 4B | Sequence Number | 이 세그먼트 첫 바이트의 스트림 내 순번 |
| 8 | 4B | Acknowledgment Number | 다음에 받을 순번 |
| 12 | 4bit | Data Offset | TCP 헤더 길이(4B 단위) |
| 12.9 | 9bit | Flags | URG·ACK·PSH·RST·SYN·FIN 등 |
| 14 | 2B | Window Size | 내가 더 받을 수 있는 버퍼 바이트 수 |
| 16 | 2B | Checksum | TCP 헤더 + 페이로드 + pseudo-header 체크섬 |
| 18 | 2B | Urgent Pointer | URG 플래그 유효 시 긴급 데이터 끝 |

전형적인 핸드셰이크·종료 흐름입니다.

```
Client  SYN           ─────>           Server  SYN=1, seq=x
Client  <───          SYN+ACK                   SYN=1, ACK=1, seq=y, ack=x+1
Client  ACK           ─────>                    ACK=1, seq=x+1, ack=y+1

[정상 종료]
        FIN           ─────>
        <───          ACK
        <───          FIN
        ACK           ─────>
```

### Ethernet FCS 4B

프레임의 앞 전체(dst MAC 부터 payload 끝) 를 CRC-32 로 계산한 4바이트 체크섬을 NIC 칩이 하드웨어로 붙입니다. 수신 NIC 가 똑같이 CRC-32 를 돌려 비교하고 다르면 drop 하며 `rx_crc_errors` 카운터를 올립니다. TCP Checksum 은 end-to-end 범위·약한 합 기반이라 서로를 보완합니다.

## 수신자가 자기 것이라고 판단하는 과정

```text
NIC (MAC 레벨)
  프레임의 목적지 MAC 이 내 MAC 인가? 아니면 drop (브로드캐스트는 예외)
  EtherType=0x0800 이면 IP 계층으로 올림

IP 계층
  목적지 IP 가 내 IP 인가? 아니면 forward 또는 drop
  proto=6 이면 TCP, 17 이면 UDP 로 올림

TCP UDP 계층
  목적지 포트에 바인드된 소켓이 있는가?
  있으면 해당 소켓의 수신 큐에 payload 복사

애플리케이션
  read() recv() 로 자기 버퍼에 가져감
```

데이터 길이는 각 헤더의 "길이 필드" 에 들어 있고, 누구 것인지는 MAC·IP·포트로 계층마다 판단합니다. 그래서 같은 비트 뭉치여도 각 계층이 자기 헤더만 떼어내며 위로 올라갑니다. CSAPP 는 이 구조를 "encapsulation" 으로 설명합니다.
