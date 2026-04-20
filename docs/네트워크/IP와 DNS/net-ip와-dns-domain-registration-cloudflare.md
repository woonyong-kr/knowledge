---
title: DNS 와 도메인 등록 — Cloudflare 로 접속이 되기까지
category: 네트워크
keyword: IP와 DNS
created: 2026-04-20
updated: 2026-04-20
tags: [dns, domain, registrar, cloudflare, resolver, authoritative, ttl]
summary: 도메인 구매와 DNS 레코드 등록, 그리고 브라우저 접속 시 재귀 조회로 IP 를 알아내는 전체 흐름을 Cloudflare 예시로 짚습니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q03-dns-domain-cloudflare.md
---

## DNS 의 용도

DNS(Domain Name System) 는 "사람이 읽는 도메인 이름 ↔ 기계가 쓰는 IP 주소" 를 매핑하는 전 세계 분산 데이터베이스입니다. 인터넷의 주소록 역할을 합니다. 용도는 크게 네 가지입니다.

- A·AAAA 레코드 : 도메인 → IPv4·IPv6 매핑. 가장 기본 용도입니다.
- CNAME : 도메인 → 다른 도메인 별칭. 예) `www.example.com → example.com`.
- MX : 메일 서버 호스트. 이메일 라우팅에 사용합니다.
- TXT : 임의 텍스트. 도메인 소유권 증명(SPF, DKIM, ACME challenge 등) 에 씁니다.

DNS 가 없으면 사람이 IP 를 외워야 하고 서버 주소가 바뀔 때마다 모든 클라이언트 설정을 갱신해야 합니다. DNS 가 있기에 "도메인 이름" 이라는 간접 참조 계층을 한 층 두고, IP 가 바뀌어도 DNS 만 고치면 됩니다.

## 등록과 해석의 두 세계

등록 쪽은 계약·권한의 세계입니다.

```text
ICANN (전체 규칙 관리)
   │
   v
Registry (TLD 관리: .com 은 Verisign, .kr 은 KISA 등)
   │
   v
Registrar (도메인 판매자: Cloudflare, GoDaddy, Gabia ...)
   │
   v
Registrant (도메인 구매자)
```

내가 `example.net` 을 사면 Registrar 가 Registry 에 "이 도메인의 네임서버는 X" 로 등록해 줍니다. 이 "네임서버 지정(NS record)" 이 도메인 권한 위임의 핵심입니다. 누군가 `example.net` 을 질의하면 `.net` TLD 네임서버가 "그건 X 네임서버에 물어봐라" 라고 안내합니다.

해석(resolve) 쪽은 질의·응답의 세계입니다. 클라이언트가 `www.example.net` 을 풀 때 아래 순서로 재귀 질의가 일어납니다.

```text
브라우저
   │  1. getaddrinfo("www.example.net")
   v
stub resolver (libc)
   │  2. /etc/hosts, /etc/nsswitch.conf 확인
   │  3. /etc/resolv.conf 의 DNS 서버에 UDP 53 질의
   v
Recursive resolver  (ISP 또는 1.1.1.1, 8.8.8.8)
   │
   │  4. 캐시 miss 이면 루트로 올라감
   v
Root nameserver (.) ── "com 은 .com TLD 에 물어봐"
   │
   v
TLD nameserver (.net) ── "example.net 은 ns1.cloudflare.com"
   │
   v
Authoritative nameserver (Cloudflare) ── "www.example.net 은 208.216.181.15"
   │
   v
Recursive resolver ──> stub resolver ──> 브라우저
                                          │
                                          v
                                     connect(208.216.181.15:80)
```

직접 확인하는 명령입니다.

```bash
$ dig www.example.net +trace
$ nslookup www.example.net
```

포인트 세 가지를 기억해 둡니다.

- DNS 는 UDP 포트 53 을 기본으로 쓰고, 대용량 응답은 TCP 53 을 씁니다. 최근에는 DoT(853, TCP·TLS), DoH(443, HTTPS) 도 자주 사용합니다.
- 각 응답에는 TTL 이 있어 일정 시간 동안 resolver 가 캐싱합니다. DNS 변경이 전 세계에 반영되는 데 시간이 걸리는 이유가 이것입니다.
- 같은 도메인을 여러 IP 로 응답할 수 있습니다(round-robin, GeoDNS).

## Cloudflare 로 접속이 되기까지의 단계

등록 단계는 사람이 하는 작업입니다.

```text
1) Cloudflare Registrar 에서 example.net 구매
     ㄴ ICANN 규정대로 WHOIS 정보 입력
     ㄴ Cloudflare 가 .net Registry(Verisign) 에 소유 사실 기록

2) Cloudflare 가 .net TLD 에 NS 레코드 등록
     example.net.   IN NS   nina.ns.cloudflare.com
     example.net.   IN NS   tom.ns.cloudflare.com

3) Cloudflare DNS 대시보드에서 레코드 추가
     www.example.net   A     208.216.181.15   (TTL 300)
     example.net       A     208.216.181.15
     example.net       MX    10 mail.example.net

4) 레코드가 Cloudflare 의 authoritative nameserver 에 저장됨
```

조회 단계는 사용자가 브라우저로 접속할 때 일어납니다.

```text
사용자가 브라우저에 http://www.example.net 입력

1) 브라우저·OS 캐시 확인 -> miss
2) stub resolver 가 /etc/resolv.conf 의 nameserver 에 질의
     -> ISP resolver 또는 1.1.1.1
3) recursive resolver 가 루트 -> .net -> Cloudflare NS 까지 재귀 질의
4) Cloudflare NS 가 www.example.net -> 208.216.181.15 응답 (+ TTL)
5) 브라우저가 208.216.181.15:80 으로 TCP connect + HTTP GET
6) 서버가 HTML 응답 -> 렌더링
```

Cloudflare 가 특별한 이유는 두 가지입니다.

- Registrar + Authoritative NS + CDN 프록시가 한 몸이라 "도메인을 사면 자동으로 CF 네임서버에 붙는" 일관된 경험을 제공합니다.
- "Proxied"(주황색 구름) 상태로 둔 레코드는 실제 IP 가 아니라 Cloudflare 자체 엣지 IP 가 응답됩니다. 외부에서 보면 `www.example.net → 104.x.x.x (Cloudflare 엣지)` 로 보이고, Cloudflare 가 뒤에서 오리진 서버(`208.216.181.15`) 로 요청을 대신 보냅니다. 이 구조가 DDoS 완화·캐싱·TLS 종단 역할까지 하는 근거입니다.

정리하면 "도메인을 샀다" 는 registrar 가 TLD 에 NS 권한을 등록해 준 것이고, "DNS 에 등록했다" 는 그 NS 에 A·CNAME·MX 레코드를 써둔 것입니다. 브라우저 접속은 이 둘을 따라 재귀 질의로 IP 를 알아낸 뒤 TCP·HTTP 로 이어집니다.
