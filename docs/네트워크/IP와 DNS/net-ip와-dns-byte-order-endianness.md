---
title: IP 주소와 바이트 순서 — IPv4·IPv6·엔디언 변환 함수
category: 네트워크
keyword: IP와 DNS
created: 2026-04-20
updated: 2026-04-20
tags: [ipv4, ipv6, byte-order, endian, htons, htonl, cidr, nat]
summary: IPv4 32비트가 전 세계 주소를 커버하는 세 가지 요소와 IPv6 형식, 그리고 htons·htonl 같은 바이트 순서 변환 함수를 왜 반드시 써야 하는지 정리합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q02-ip-address-byte-order.md
---

## IPv4 32비트로 전 세계를 커버하는 세 가지 요소

IPv4 주소는 `uint32_t` 한 개, 즉 약 42.9억(2^32) 개 주소가 전부입니다. 사람이 읽기 편하도록 1바이트씩 끊어 `a.b.c.d` 로 적은 것이 dotted-decimal notation 입니다. 이 크기만으로 전 세계를 커버할 수 있는 이유는 세 가지 요소가 합쳐진 결과입니다.

첫째, 계층적 할당입니다. IANA 가 RIR(지역 인터넷 레지스트리) 에 큰 블록을 주고, RIR 이 사업자에게, 사업자가 조직에 주는 식입니다. 각 조직은 받은 블록(예: `128.2.0.0/16` = 65,536개) 을 내부에서 서브넷으로 나눠 씁니다. 라우팅은 주소가 아니라 블록(prefix) 단위로 이뤄지므로 라우팅 테이블이 훨씬 작아집니다.

둘째, CIDR(Classless Inter-Domain Routing) 입니다. 예전의 고정 A·B·C 클래스 대신 `/24`, `/16`, `/29` 처럼 프리픽스 길이를 자유롭게 지정합니다.

```text
128.2.194.242  ->  이진수로
10000000.00000010.11000010.11110010

/16 프리픽스면:  128.2.0.0/16   (앞 16비트가 같은 65,536개)
/24 프리픽스면:  128.2.194.0/24 (앞 24비트가 같은 256개)
```

셋째, NAT(Network Address Translation) 입니다. 42.9억은 이미 수백억 디바이스에 비해 부족합니다. 실제로는 집·회사에서 사설 주소(`10.x`, `172.16~31.x`, `192.168.x`) 를 쓰고, 게이트웨이가 나갈 때만 공인 IP 한 개로 바꿔 줍니다. 안쪽 프로세스 수십만 개가 공인 IP 1개 + 서로 다른 포트로 매핑됩니다.

## IPv4 와 IPv6 의 차이

```text
IPv4
  크기     : 32 비트 = 4 바이트
  형식     : a.b.c.d  (각 0~255)
  공간     : 약 4.29 × 10^9
  구조체   : struct in_addr  { uint32_t s_addr; }

IPv6
  크기     : 128 비트 = 16 바이트
  형식     : 8개의 16비트 hextet 을 ":" 로 연결
             예) 2001:0db8:85a3:0000:0000:8a2e:0370:7334
             연속된 0 은 "::" 로 한 번만 축약 가능
             -> 2001:db8:85a3::8a2e:370:7334
  공간     : 약 3.4 × 10^38
  구조체   : struct in6_addr { uint8_t s6_addr[16]; }
```

실무에서 덧붙일 차이점입니다.

- IPv6 에는 브로드캐스트가 없고 멀티캐스트로 대체됐습니다.
- IPv6 헤더는 고정 40B 로 단순화됐고, 옵션은 확장 헤더로 분리됩니다.
- IPv6 는 NAT 없이도 주소가 충분해 호스트가 직접 공인 주소를 가질 수 있습니다.
- `getaddrinfo` 는 이 두 버전을 모두 다루기 위한 프로토콜 독립 인터페이스입니다. `sockaddr_storage` 와 `ai_family = AF_INET | AF_INET6 | AF_UNSPEC` 가 핵심 장치입니다.

## 바이트 순서 변환 함수가 필요한 이유

네트워크는 빅엔디언(big-endian) 을 표준 바이트 순서로 씁니다. 반면 x86·ARM(Apple silicon 포함) 계열 CPU 의 메모리 표현은 리틀엔디언(little-endian) 입니다. 이 차이를 맞추는 도구가 다음 네 함수입니다.

- `htons` : host → network short(16-bit) — 포트 번호 변환
- `htonl` : host → network long(32-bit) — IPv4 주소 변환
- `ntohs` : network → host short
- `ntohl` : network → host long

포트 80(`0x0050`) 을 리틀엔디언 x86 메모리에 그대로 쓰면 어떻게 되는지 봅니다.

```text
uint16_t port = 80;            // 0x0050
메모리 바이트 배열(LE):         [0x50, 0x00]

네트워크 상에서 80 을 쓰려면 BE 로:   [0x00, 0x50]
htons(80) = 0x5000             // BE 표현을 LE 레지스터에 담으면 이렇게 보임

sin_port = htons(80);          // 소켓 구조체에는 이대로 들어가야 함
```

만약 변환 없이 `sin_port = 80` 으로 직접 넣으면 다음과 같이 엉뚱한 결과가 나옵니다.

```text
sin_port 의 바이트들(LE 메모리):  [0x50, 0x00]
네트워크로 그대로 나가면 상대는 BE 로 해석 -> 0x5000 = 20480
=> 서버는 20480 포트로 연결 시도한 것으로 인식
```

포트·주소를 소켓 구조체에 넣을 때는 반드시 host order → network order 변환을 거쳐야 합니다. 반대로 패킷에서 읽어온 값을 비교·출력할 때는 `ntohs`·`ntohl` 로 host order 로 돌려야 사람이 기대하는 값이 나옵니다. 64비트 변환 함수(`htonll`) 는 표준에 없어 필요 시 직접 구현합니다. IP·포트는 최대 32비트라 `htonl`·`htons` 까지만 있어도 충분합니다.

IP 주소 문자열 ↔ 바이너리 변환은 별도 함수가 담당합니다.

- `inet_pton(AF_INET, "128.2.194.242", &dst)` 로 `struct in_addr` 에 BE 로 채웁니다.
- `inet_ntop(AF_INET, &src, buf, INET_ADDRSTRLEN)` 로 사람이 읽는 문자열로 돌립니다.
