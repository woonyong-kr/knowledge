---
title: Sockets Interface — addrinfo 와 서버·클라이언트 호출 순서
category: 네트워크
keyword: 소켓 시스템콜
created: 2026-04-20
updated: 2026-04-20
tags: [socket, bind, listen, accept, connect, getaddrinfo, addrinfo]
summary: 서버와 클라이언트의 소켓 함수 호출 생명주기를 나란히 정리하고, `getaddrinfo` 가 돌려주는 `addrinfo` 연결 리스트의 각 필드 의미와 사용법을 살펴봅니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q06-ch11-4-sockets-interface.md
---

## 서버와 클라이언트의 호출 순서

생명주기를 나란히 놓으면 한눈에 들어옵니다.

```text
─── 서버 ──────────────────────    ─── 클라이언트 ────────────────
getaddrinfo(host, port, hints, &r)    getaddrinfo(host, port, hints, &r)
   └ AI_PASSIVE 로 wildcard 요구         └ hints 는 보통 AF_UNSPEC
listenfd = socket(...)                clientfd = socket(...)
setsockopt(SO_REUSEADDR, 1)           (옵션 설정은 선택)
bind(listenfd, addr)                        │
listen(listenfd, backlog)                   │
freeaddrinfo(r)                       connect(clientfd, addr)
while (1) {                           freeaddrinfo(r)
  connfd = accept(listenfd,           read·write(clientfd, buf, n)
                  &cli, &clilen)      close(clientfd)
  read·write(connfd, buf, n)
  close(connfd)
}
close(listenfd)
```

각 함수의 한 줄 요약입니다.

- `socket(AF_INET, SOCK_STREAM, 0)` : fd 만 생성합니다. 아직 주소도 상대도 모릅니다.
- `bind(fd, addr, len)` : 로컬 주소(IP·port) 를 fd 에 묶습니다. 주로 서버가 호출합니다.
- `listen(fd, backlog)` : fd 를 passive listener 로 전환합니다. 커널이 SYN 큐와 accept 큐를 만듭니다.
- `accept(fd, &cli, &clilen)` : accept 큐에서 연결 하나를 꺼내 새 fd(`connfd`) 를 반환합니다. `listenfd` 는 그대로 남습니다.
- `connect(fd, addr, len)` : 서버로 SYN 을 보내고 3-way handshake 완료까지 블록됩니다.
- `read`·`write` : 커널 소켓 버퍼에서 읽고 씁니다. 파일과 동일한 API 입니다.
- `close(fd)` : 참조 카운트 -1, 0 이 되면 FIN 을 보내고 소켓을 해제합니다.
- `getaddrinfo`·`getnameinfo` : host·service 문자열 ↔ `struct sockaddr` 변환(프로토콜 독립) 입니다.
- `setsockopt(SO_REUSEADDR, 1)` : 서버 재시작 시 "Address already in use" 를 방지합니다.
- CSAPP 의 래퍼 `open_clientfd`·`open_listenfd` 는 위 루틴을 각각 한 줄로 묶은 것입니다.

상태 전이는 다음과 같습니다.

```text
서버 소켓
  created -> bind -> LISTEN -> (SYN 받음) -> (3WHS 완료, accept 큐에 올림)
          -> accept -> ESTABLISHED connfd 하나 반환

클라 소켓
  created -> connect 호출 -> SYN_SENT -> (SYN-ACK 받음) -> ESTABLISHED
```

## open_clientfd 구현 예

CSAPP 의 `open_clientfd` 와 거의 같은 형태입니다.

```c
int open_clientfd(char *hostname, char *port)
{
    int clientfd;
    struct addrinfo hints, *listp, *p;

    /* 1) hints 로 원하는 소켓 모양을 지정 */
    memset(&hints, 0, sizeof(hints));
    hints.ai_socktype = SOCK_STREAM;      /* TCP */
    hints.ai_flags    = AI_NUMERICSERV;   /* port 는 숫자 문자열 */
    hints.ai_flags   |= AI_ADDRCONFIG;    /* 내 호스트에 설정된 AF 만 */

    /* 2) hostname + port -> addrinfo linked list */
    Getaddrinfo(hostname, port, &hints, &listp);

    /* 3) 리스트를 순회하며 socket + connect 시도 */
    for (p = listp; p; p = p->ai_next) {
        if ((clientfd = socket(p->ai_family,
                               p->ai_socktype,
                               p->ai_protocol)) < 0)
            continue;   /* 이 조합은 생성 실패 -> 다음 후보 */

        if (connect(clientfd, p->ai_addr, p->ai_addrlen) != -1)
            break;      /* 성공 -> 루프 탈출 */

        Close(clientfd); /* 실패 -> 닫고 다음 후보 */
    }

    /* 4) 반드시 freeaddrinfo */
    Freeaddrinfo(listp);

    if (!p)         /* 모든 후보 실패 */
        return -1;
    return clientfd;
}
```

의미를 정리합니다.

- `getaddrinfo` 는 host·service 문자열만 알면 DNS 도 돌리고 `sockaddr` 도 채워 주는 준비물 공장입니다. 후보가 여러 개(IPv4·IPv6, 여러 DNS 응답) 올 수 있어 연결 리스트로 돌려줍니다.
- `socket()` 은 준비물의 `(ai_family, ai_socktype, ai_protocol)` 을 그대로 받아 fd 만 만듭니다.
- `connect()` 는 준비물의 `(ai_addr, ai_addrlen)` 을 그대로 써서 서버로 연결합니다.

즉 "getaddrinfo → socket → connect" 는 준비물 생성 → 도구 만들기 → 실제 연결의 세 단계이고, 서버는 `connect` 대신 `bind`·`listen`·`accept` 가 들어갑니다.

## struct addrinfo 의 필드

```c
struct addrinfo {
    int              ai_flags;      /* Hints argument flags */
    int              ai_family;     /* socket 의 첫 번째 인자 */
    int              ai_socktype;   /* socket 의 두 번째 인자 */
    int              ai_protocol;   /* socket 의 세 번째 인자 */
    char            *ai_canonname;  /* Canonical hostname */
    size_t           ai_addrlen;    /* Size of ai_addr struct */
    struct sockaddr *ai_addr;       /* Ptr to socket address structure */
    struct addrinfo *ai_next;       /* 다음 후보 노드 */
};
```

필드별 의미와 실제 쓰임입니다.

```text
ai_flags     | hints 로 "원하는 결과" 를 지정하는 비트 플래그
             | AI_PASSIVE       -> bind 용 wildcard 주소(INADDR_ANY) 반환
             | AI_ADDRCONFIG    -> 로컬에 구성된 AF 만 반환
             | AI_NUMERICSERV   -> service 인자를 숫자 포트로만 해석
             | AI_NUMERICHOST   -> hostname 을 IP 문자열로만 해석, DNS 안 함
             | AI_V4MAPPED      -> IPv6 소켓에서 IPv4-mapped 주소 반환

ai_family    | 주소 체계
             | AF_INET  = IPv4, AF_INET6 = IPv6, AF_UNSPEC = 둘 다 허용(권장)
             | -> socket() 의 첫 번째 인자

ai_socktype  | 소켓 타입
             | SOCK_STREAM = TCP, SOCK_DGRAM = UDP, SOCK_RAW = raw
             | -> socket() 의 두 번째 인자

ai_protocol  | 프로토콜
             | 보통 0 (STREAM->TCP, DGRAM->UDP)
             | IPPROTO_TCP, IPPROTO_UDP 로 명시 가능
             | -> socket() 의 세 번째 인자

ai_canonname | 호스트 이름의 canonical 형태 (CNAME 풀어낸 실제 이름)
             | AI_CANONNAME 플래그 지정 시만 채워짐

ai_addrlen   | ai_addr 크기 (IPv4 sockaddr_in=16B, IPv6 sockaddr_in6=28B)
             | -> connect·bind 의 addrlen 인자

ai_addr      | 실제 소켓 주소 구조체 포인터 (struct sockaddr*)
             | 내부는 sockaddr_in 또는 sockaddr_in6
             | 포트·IP 가 network byte order 로 이미 채워져 있음
             | -> connect·bind 의 addr 인자

ai_next      | 다음 후보 노드를 가리키는 포인터
             | DNS 가 여러 IP 를 주거나 IPv4·IPv6 둘 다일 때
             | 리스트로 돌려줌 -> 순회하며 첫 번째 성공 조합을 사용
```

hints 의 값과 결과 `addrinfo` 가 같은 구조체를 쓰는 게 처음엔 혼란스럽지만, "호출자가 빈 구조체에 원하는 필터(flags·family·socktype) 만 채워서 주면, 커널이 그걸 만족하는 후보를 연결 리스트로 돌려준다" 로 이해하면 됩니다. 결과를 다 쓰고 나면 반드시 `freeaddrinfo(listp)` 로 리스트를 해제해야 누수가 없습니다.
