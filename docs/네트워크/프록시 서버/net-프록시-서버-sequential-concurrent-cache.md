---
title: 프록시 서버 — Tiny 를 확장한 순차·동시·캐싱 모델
category: 네트워크
keyword: 프록시 서버
created: 2026-04-20
updated: 2026-04-20
tags: [proxy, forward-proxy, reverse-proxy, caching, cdn, tunnel, proxy-lab]
summary: 프록시는 "동시에 서버이자 클라이언트" 입니다. CSAPP Tiny 의 뼈대를 재활용해 요청을 파싱하고 상위 서버로 중계하는 구조, 캐시·동시성 확장, 포워드·리버스·CDN 배치 차이를 정리합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q15-proxy-extension.md
---

# 프록시 서버 — Tiny 를 확장한 순차·동시·캐싱 모델

프록시는 클라이언트와 오리진 서버 사이에 끼어서 요청을 대신 받고 상위 서버로 중계하는 서버입니다. CSAPP Proxy Lab 은 Tiny 의 `main` 과 `doit` 구조를 그대로 쓰되, `serve_static`·`serve_dynamic` 대신 "상위 서버에 연결해서 응답을 릴레이" 로 바꾸는 실습입니다.

## 프록시는 서버이자 클라이언트

프록시 한 프로세스가 한 번의 요청을 처리하는 동안 두 가지 역할을 번갈아 합니다.

```text
클라이언트              프록시                         오리진 서버
    |   HTTP 요청         |                                  |
    |-------------------->|                                  |
    |                     |  URL 파싱 -> host:port 추출      |
    |                     |  open_clientfd(host, port)       |
    |                     |  (HTTP/1.1 -> HTTP/1.0 변환,      |
    |                     |   Connection: close 강제)         |
    |                     |         HTTP 요청 (변환본)        |
    |                     |--------------------------------->|
    |                     |         HTTP 응답                 |
    |                     |<---------------------------------|
    |     HTTP 응답        |                                  |
    |<--------------------|                                  |
```

한 프로세스 안에서 `open_listenfd` (서버 역할) 와 `open_clientfd` (클라이언트 역할) 가 동시에 쓰이는 것이 프록시의 본질입니다.

## 네 가지 배치 방식

역할에 따라 다음 네 종류가 있습니다.

- 포워드 프록시 — 사내망에서 바깥 인터넷으로 나갈 때 거치는 프록시입니다. 필터링·감사·캐싱이 목적이며 클라이언트가 프록시 주소를 명시적으로 설정합니다.
- 리버스 프록시 — 외부 요청을 내부 서버들로 분배합니다. Nginx·Cloudflare·AWS ALB 가 대표적이며 클라이언트는 프록시를 진짜 서버로 알고 있습니다.
- 캐싱 프록시 — 이전 응답을 저장했다가 같은 요청에 재사용합니다. Squid·Varnish·CDN 엣지가 여기 해당합니다.
- 터널 프록시 — `CONNECT` 메서드로 TCP 파이프를 만들어 TLS 트래픽을 통째로 중계합니다. HTTPS 프록시의 기본 동작입니다.

```text
[ 포워드 ]   사내 PC -> 포워드 프록시 -> 인터넷 -> 서버
[ 리버스 ]   인터넷 -> 리버스 프록시 -> 내부 서버 (여러 대)
[ CDN ]      클라이언트 -> CDN 엣지(캐싱 프록시) -> 오리진
```

CSAPP Proxy Lab 은 학습 목적상 포워드 + 캐싱 프록시 조합을 다룹니다. HTTP 요청을 만드는 쪽과 받는 쪽을 모두 구현하는 것이 핵심이기 때문입니다.

## Tiny 에서 바뀌는 부분

`doit` 의 내부만 다음과 같이 바뀝니다. 바깥 `main` 과 accept 루프는 Tiny 와 동일합니다.

```text
doit
  - Rio_readlineb 로 요청 라인 읽기        <- Tiny 와 동일
  - 요청 파싱
      요청 라인: GET <URL> HTTP/1.1
      여기서 URL 은 절대 URL:
        GET http://www.example.net:80/home.html HTTP/1.1
      -> host, port, path 로 쪼갠다
  - 헤더 읽기 + 변환
      - HTTP/1.1 -> HTTP/1.0 교체
      - Connection: close 강제
      - Proxy-Connection: close 강제
      - Host 없으면 추가
      - User-Agent 를 고정값으로 덮는 경우도 있음
  - open_clientfd(host, port) 로 오리진 연결
  - 변환된 요청을 오리진에 Rio_writen
  - 오리진 응답을 Rio_readnb 로 읽어 connfd 에 Rio_writen
  - 양쪽 fd close
```

즉 "응답을 어떻게 만드느냐" 부분만 상위 서버에서 가져오는 방식으로 바뀌고, 나머지 구조는 Tiny 를 그대로 계승합니다.

## 캐싱 프록시 확장

응답을 로컬에 저장해 재사용하는 단계입니다.

```text
- 요청 파싱 후 캐시 lookup (key = URL 또는 host+path)
- HIT  : 저장된 응답을 바로 클라이언트에 전송하고 종료
- MISS : 오리진에서 가져와 전달하면서 메모리에 저장
- MAX_OBJECT_SIZE 초과면 저장 스킵
- 전체 캐시가 가득 차면 LRU 로 eviction
- 공유 자료구조이므로 readers-writers lock 필요
```

## 동시성 확장

두 번째 단계는 멀티클라이언트 처리입니다.

```text
- main : accept 만 담당, connfd 를 작업 큐에 넣거나 pthread_create 로 분사
- worker: detached thread (join 불필요)
- 각 worker 가 doit(connfd) 를 호출하고 close
```

순차 → 동시 → 캐싱 세 단계가 프록시 서버 구현의 표준 진화 경로입니다. 이 패턴은 SQL API 서버처럼 "상위 서버 대신 DB 엔진이 응답을 만든다" 는 반대 방향 구조에도 그대로 적용됩니다.

## 요점

프록시의 실체는 "서버로 받아서 클라이언트로 다시 보낸다" 는 한 줄입니다. Tiny 의 accept 루프와 래퍼 함수를 그대로 쓰면서 응답 생성 경로만 상위 서버 중계로 바꾸면 순차 프록시가 완성되고, 여기에 캐시와 스레드 풀을 얹으면 실전 프록시 서버의 3단 구조가 만들어집니다.
