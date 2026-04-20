---
title: HTTP·FTP·MIME·Telnet 과 HTTP 1.0 대 1.1 차이
category: 네트워크
keyword: HTTP 프로토콜
created: 2026-04-20
updated: 2026-04-20
tags: [http, ftp, mime, telnet, keep-alive, chunked, persistent]
summary: FTP 와 HTTP 의 설계 차이, MIME 타입이 하는 역할, Telnet 이 모든 TCP 텍스트 프로토콜의 범용 클라이언트인 이유, 그리고 HTTP 1.0 과 1.1 의 차이를 정리합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q11-http-ftp-mime-telnet.md
---

## FTP 와 HTTP 의 설계 차이

FTP(RFC 959) 는 파일 전송 전용 프로토콜이고, HTTP(RFC 2616 등) 는 하이퍼텍스트 문서를 요청·응답으로 주고받는 범용 애플리케이션 프로토콜입니다. 둘 다 TCP 위에서 텍스트 기반 명령으로 동작하지만 설계 철학이 다릅니다.

```text
                   FTP                                HTTP
-----------------------------------------------------------------------
포트              제어 21, 데이터 20 (active)          80, 443(TLS)
                  또는 passive 동적 포트
연결 수           두 개 (control + data)              기본 한 개
상태              세션 기반 (USER, PASS, CWD...)       stateless (쿠키로 보완)
명령              ASCII 명령: USER, RETR, STOR, LIST   METHOD URI VERSION + 헤더
응답              3자리 상태코드 + 텍스트 (예: 220)    3자리 상태코드 + 헤더 + body
용도              파일 업·다운로드 전용                 웹 전반(HTML, 이미지, API)
특수              Active·Passive 모드 (NAT 어려움)     CONNECT, WebSocket 등 확장 많음
```

핵심 차이는 세 가지입니다. 첫째, FTP 는 제어 연결과 데이터 연결이 분리돼 있어 NAT·방화벽 친화적이지 않고, HTTP 는 한 연결에 다 담습니다. 둘째, FTP 는 stateful 로 "지금 어떤 디렉터리인지", "로그인 됐는지" 를 서버가 기억하지만 HTTP 는 매 요청이 독립적입니다. 셋째, HTTP 는 MIME 타입으로 다양한 콘텐츠를 실을 수 있어서 하이퍼텍스트뿐 아니라 API·파일 다운로드까지 커버합니다. 오늘날 FTP 자리는 SFTP·SCP·Object Storage 가 거의 대체했습니다.

## MIME 타입이 하는 일

MIME(Multipurpose Internet Mail Extensions) 타입은 원래 이메일이 텍스트뿐 아니라 이미지·첨부 파일을 실어 보내도록 만든 표준인데, HTTP 가 그대로 이어받았습니다. "이 바이트 덩어리가 어떤 종류의 콘텐츠인가" 를 서버가 명시하는 레이블입니다.

HTTP 응답에서는 `Content-Type` 헤더로 전달합니다.

```text
Content-Type: text/html; charset=utf-8
Content-Type: image/png
Content-Type: application/json
Content-Type: video/mpeg
Content-Type: application/octet-stream
```

형식은 `type/subtype` 이고 `text`·`image`·`audio`·`video`·`application`·`multipart` 등의 대분류가 있습니다. 필요한 이유는 세 가지입니다. 브라우저가 어떻게 렌더링할지 결정하는 기준이 되고(`text/html` 이면 파서로, `image/png` 이면 이미지로, `application/octet-stream` 이면 저장 다이얼로그), 파일 확장자에만 의존하지 않으며(URL 이 `.html` 로 끝나도 `Content-Type: text/plain` 이면 텍스트로 보여줌), 보안 측면에서 `X-Content-Type-Options: nosniff` 와 결합해 브라우저의 임의 추측을 막습니다.

Tiny 서버의 `get_filetype()` 함수가 하는 일이 정확히 이 매핑입니다. 확장자를 보고 `Content-Type` 값을 결정해 응답 헤더에 넣습니다.

## Telnet 이 범용 클라이언트인 이유

Telnet 은 원래 원격 로그인 프로토콜(포트 23) 입니다. 지금은 보안 문제로 거의 쓰지 않지만(대신 SSH), `telnet` 이라는 CLI 도구는 여전히 유용합니다. 이 도구가 "지정한 호스트·포트로 TCP 소켓을 열고, stdin 을 소켓에 밀어넣고, 소켓에서 읽은 것을 stdout 에 찍는" 동작을 하기 때문입니다. TCP 기반 텍스트 프로토콜이면 무엇이든 사람 손으로 칠 수 있는 범용 클라이언트가 됩니다. HTTP·SMTP·POP3·IMAP·Redis RESP 같은 것 전부입니다.

HTTP 를 손으로 쳐 보면 이렇습니다.

```text
$ telnet www.example.net 80
Trying 208.216.181.15...
Connected to www.example.net.
Escape character is '^]'.
GET /home.html HTTP/1.0
Host: www.example.net

HTTP/1.0 200 OK
Server: Tiny Web Server
Content-length: 2048
Content-type: text/html

<html>...
```

SMTP 도 같은 방식입니다.

```text
$ telnet mail.example.com 25
220 mail.example.com ESMTP ready
HELO test
250 Hello
MAIL FROM:<a@x.com>
250 OK
...
```

CSAPP 11.5 가 "Telnet 으로 HTTP 요청을 직접 쳐 보라" 고 한 이유가 이것입니다. 소켓 한 개로 양방향 텍스트를 주고받는 구조라 프로토콜 디버깅 도구로 완벽합니다. 요즘은 `nc`(netcat), `curl -v`, `openssl s_client`(TLS 용) 가 같은 역할을 합니다.

## HTTP 1.0 과 1.1 의 차이

핵심만 뽑으면 다음과 같습니다.

```text
                    HTTP/1.0                        HTTP/1.1
--------------------------------------------------------------------------
기본 연결           요청마다 새 TCP (close)         persistent (keep-alive)
Host 헤더           선택                            필수 (가상 호스팅)
파이프라이닝        X                               O (순서 보장 필요)
chunked encoding    X                               O (Transfer-Encoding)
캐시 제어           Expires 위주                    Cache-Control 세분화
range 요청          제한적                          Range·Content-Range
추가 메서드         GET·HEAD·POST                   + PUT·DELETE·OPTIONS·TRACE
호스트당 연결 수    보통 1                          2~6 병렬
```

CSAPP 가 11.6 Tiny 에서 다루는 과제는 1.1 요청을 받아도 1.0 으로 응답하는 형태입니다. 구현 단순성 때문입니다. 1.0 으로 응답하면 매 요청마다 연결이 끊기므로 `Content-Length` 만 정확히 쓰고 `Connection: close` 만 지키면 됩니다. 1.1 을 완전히 구현하려면 keep-alive 상태 관리, chunked encoding, 파이프라이닝 에러 처리가 추가로 필요합니다.

HTTP/2 는 바이너리 프레이밍과 멀티플렉싱을 도입했고, HTTP/3 는 UDP 기반 QUIC 위로 옮겼습니다. 실무에서는 오리진 서버가 HTTP/1.1 로 말해도 Cloudflare 같은 프록시가 클라이언트와는 HTTP/2·3 으로 말해주는 구성이 흔합니다.
