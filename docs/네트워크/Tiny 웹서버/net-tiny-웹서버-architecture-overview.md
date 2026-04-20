---
title: Tiny 웹서버 — main·doit·parse_uri·serve_static·serve_dynamic 전체 흐름
category: 네트워크
keyword: Tiny 웹서버
created: 2026-04-20
updated: 2026-04-20
tags: [tiny, http, parse-uri, serve-static, serve-dynamic, cgi, mmap]
summary: CSAPP 11.6 Tiny 서버의 함수 호출 트리(main·doit·parse_uri·serve_static·serve_dynamic·clienterror) 를 정리하고, 정적·동적 요청 두 경로를 코드와 함께 따라갑니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q12-tiny-web-server.md
---

## Tiny 가 하는 일

Tiny 는 CSAPP 가 제공하는 가장 단순한 완결 HTTP/1.0 서버입니다. 약 300 줄의 C 코드로 세 가지를 합니다.

- TCP 로 지정 포트에서 listen 하고 순차적으로 연결을 받습니다(iterative server).
- `GET` 메서드만 지원해 디스크 파일을 돌려줍니다(정적 콘텐츠).
- URI 에 `cgi-bin` 이 포함되면 `fork`·`execve` 로 해당 프로그램을 실행해 결과를 돌려줍니다(동적 콘텐츠).

교재용 참조 구현이라 의도적으로 단순하고 HTTPS·keep-alive·POST·SIGCHLD 처리는 숙제로 남깁니다. 대신 진짜 웹 서버의 뼈대는 여기 다 들어 있고, Proxy Lab 과 SQL API 서버도 Tiny 의 main 루프 모양을 재사용합니다.

## 함수 호출 트리

```text
main
 ├─ Open_listenfd(port)          <- socket + bind + listen 래퍼
 └─ while (1)
     ├─ Accept(listenfd, ...)    <- 연결 하나 받기, connfd 반환
     ├─ Getnameinfo(...)         <- 클라 이름·포트 로깅
     ├─ doit(connfd)             <- 한 요청 처리
     └─ Close(connfd)

doit
 ├─ Rio_readinitb + Rio_readlineb   <- 요청 라인 읽기
 ├─ sscanf -> method, uri, version
 ├─ method != GET -> clienterror(501)
 ├─ read_requesthdrs(&rio)           <- 나머지 헤더 소비(파싱 안 함)
 ├─ parse_uri(uri, filename, cgiargs)  -> is_static
 ├─ stat(filename, &sbuf)              -> 없으면 clienterror(404)
 ├─ is_static
 │    ├─ S_ISREG && S_IRUSR           <- 일반 파일 + 읽기 가능
 │    │    └─ 아니면 clienterror(403)
 │    └─ serve_static(fd, filename, size)
 └─ dynamic
      ├─ S_ISREG && S_IXUSR           <- 일반 파일 + 실행 가능
      │    └─ 아니면 clienterror(403)
      └─ serve_dynamic(fd, filename, cgiargs)

parse_uri
 ├─ strstr(uri, "cgi-bin") == NULL
 │    ├─ cgiargs 비우기
 │    ├─ filename = "." + uri
 │    ├─ 마지막이 '/' 이면 home.html 을 덧붙임
 │    └─ 반환 1 (static)
 └─ else (dynamic)
      ├─ '?' 찾아 쿼리스트링 분리 -> cgiargs
      └─ 반환 0 (dynamic)

serve_static
 ├─ get_filetype(filename, filetype)
 ├─ 응답 라인·헤더 조립 후 Rio_writen
 ├─ Open + Mmap -> srcp
 ├─ Close(srcfd)
 ├─ Rio_writen(fd, srcp, size)
 └─ Munmap(srcp, size)

serve_dynamic
 ├─ HTTP/1.0 200 OK + Server 헤더 전송
 ├─ Fork()
 │    └─ 자식:
 │         setenv("QUERY_STRING", cgiargs, 1)
 │         Dup2(fd, STDOUT_FILENO)
 │         Execve(filename, emptylist, environ)
 └─ Wait(NULL)

clienterror
 ├─ 작은 HTML 본문 조립
 └─ 응답 라인·헤더·본문을 바로 write
```

각 함수의 역할을 한 줄씩 정리하면 이렇습니다. `main` 은 리스닝과 accept 루프(요청 1 개 = 순회 1 회) 이고, `doit` 는 한 요청의 생명주기를 통째로 관리합니다. `read_requesthdrs` 는 1.0 이 헤더를 거의 쓰지 않기 때문에 빈 줄(`\r\n`) 까지 소비만 합니다. `parse_uri` 는 URI 만 보고 정적·동적을 결정하고 `filename`·`cgiargs` 로 분리하는데, 규칙은 `cgi-bin` 포함 여부 하나가 전부입니다. `serve_static` 은 `mmap` 으로 파일을 메모리에 매핑한 뒤 통째로 `rio_writen` 합니다. `get_filetype` 은 확장자 → MIME 타입(`.html → text/html`) 매핑이고, `serve_dynamic` 은 `fork + dup2 + execve` 로 CGI 를 실행합니다. `clienterror` 는 에러 응답 HTML 을 조립해 바로 보냅니다.

## 정적 요청 흐름

예시: `GET /home.html HTTP/1.0`

```text
1) Accept -> connfd
2) Rio_readlineb -> "GET /home.html HTTP/1.0\r\n"
3) sscanf -> method="GET", uri="/home.html", version="HTTP/1.0"
4) read_requesthdrs -> 빈 줄까지 소비
5) parse_uri:
     uri 에 "cgi-bin" 없음 -> static
     filename = "./home.html"
     cgiargs  = ""
     returns 1
6) stat("./home.html") -> sbuf.st_size = 2048, 접근 권한 OK
7) serve_static(connfd, "./home.html", 2048)
     ㄴ get_filetype -> "text/html"
     ㄴ 응답 헤더 구성
        HTTP/1.0 200 OK
        Server: Tiny Web Server
        Connection: close
        Content-length: 2048
        Content-type: text/html
        \r\n
     ㄴ Rio_writen(connfd, headers, ~91B)
     ㄴ open + mmap -> srcp
     ㄴ Rio_writen(connfd, srcp, 2048)
     ㄴ munmap
8) Close(connfd)
```

총 응답 크기는 91B + 2048B = 2139B 로, CSAPP 의 numeric walkthrough 에서 쓰는 숫자와 동일합니다.

## 동적 요청 흐름

예시: `GET /cgi-bin/adder?15000&213 HTTP/1.0`

```text
1) Accept -> connfd
2) 요청 라인 파싱
3) read_requesthdrs -> 빈 줄까지 소비
4) parse_uri:
     "cgi-bin" 포함 -> dynamic
     '?' 기준: path = "./cgi-bin/adder", cgiargs = "15000&213"
     returns 0
5) stat -> 실행 가능 확인
6) serve_dynamic(connfd, "./cgi-bin/adder", "15000&213")
     ㄴ "HTTP/1.0 200 OK\r\nServer: Tiny Web Server\r\n" 전송
     ㄴ Fork() == 0 (자식)
          setenv("QUERY_STRING", "15000&213", 1)
          Dup2(connfd, 1)                         <- stdout -> connfd
          Execve("./cgi-bin/adder", [NULL], environ)
            adder 가 getenv("QUERY_STRING") = "15000&213"
            -> 15000 + 213 = 15213 계산
            -> stdout 에 Content-* 헤더 + 본문 출력
            -> 소켓으로 바로 나감
     ㄴ Wait(NULL)
7) Close(connfd)
```

## 확장 포인트

Tiny 코드를 보면 Proxy Lab 과 SQL API 서버를 만들 때 어디를 바꿔야 하는지가 곧바로 보입니다.

- 프록시: `parse_uri` 대신 URL 파서가 들어가고, `serve_*` 대신 상위 서버로의 `connect + relay` 가 들어갑니다. `main` 루프의 모양은 그대로입니다.
- 동시성: `doit(connfd)` 를 그대로 호출하는 대신 `pthread_create` 로 스레드에 태우거나 작업 큐에 넣습니다.
- SQL API 서버: `parse_uri` 를 "요청 본문에서 SQL 문자열 추출" 로 바꾸고, `serve_*` 를 "DB 실행 + 결과 직렬화" 로 바꿉니다.
