---
title: 에코 서버와 EOF — 데이터그램 경계·파일 I/O 와의 유사성
category: 네트워크
keyword: Concurrent Server
created: 2026-04-20
updated: 2026-04-20
tags: [echo-server, datagram, eof, iterative, rio, half-close, sigpipe]
summary: 에코 서버의 골격과 TCP·UDP 의 경계 차이, 소켓에서 `read` 가 0 을 돌려주는 EOF 의미를 정리합니다. 파일 I/O 와 같은 인터페이스를 쓰면서도 half-close·short read·SIGPIPE 가 더해지는 이유를 설명합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q14-echo-server-datagram-eof.md
---

# 에코 서버와 EOF — 데이터그램 경계·파일 I/O 와의 유사성

에코 서버는 "받은 것을 그대로 돌려주는" 가장 단순한 네트워크 프로그램입니다. 코드가 짧지만 소켓 API 가 파일 I/O 와 어떻게 닮았고, 어디서부터 다른지를 한눈에 보여주는 예제입니다.

## 데이터그램과 세그먼트·프레임

계층별 전송 단위의 명칭이 겹쳐 혼란스럽습니다. 구분해서 쓰면 다음과 같습니다.

```text
L2 (링크)      frame       : 이더넷 프레임. MAC + EtherType + payload + FCS
L3 (네트워크)  packet       : IP 패킷. 좁게 쓰면 IP datagram
L4 (전송)
    TCP        segment      : byte stream 을 잘라 붙인 단위
    UDP        datagram     : 그 자체가 메시지의 최소 단위
```

핵심은 **경계 보존** 여부입니다. UDP·IP 는 한 번에 주소를 붙여 독립적으로 배달되므로 경계가 보존됩니다. 송신자가 100B 를 한 번 보내면 수신자도 정확히 100B 한 개로 받습니다. TCP 는 byte stream 이므로 경계가 없습니다. 50B 를 두 번 보내도 수신자는 100B 한 번으로 받을 수 있습니다. 이 차이가 `sendto/recvfrom` (UDP) 와 `read/write` (TCP) 의 사용을 가릅니다.

## 에코 서버의 뼈대

CSAPP 의 에코 서버는 `accept` → `echo` → `close` 를 한 루프에서 반복합니다.

```c
int main(int argc, char **argv)
{
    int listenfd, connfd;
    socklen_t clientlen;
    struct sockaddr_storage clientaddr;

    listenfd = Open_listenfd(argv[1]);   /* = socket + bind + listen */

    while (1) {
        clientlen = sizeof(struct sockaddr_storage);
        connfd = Accept(listenfd, (SA*)&clientaddr, &clientlen);
        echo(connfd);                    /* 진짜 일은 여기서 */
        Close(connfd);
    }
}

void echo(int connfd)
{
    size_t n;
    char buf[MAXLINE];
    rio_t rio;

    Rio_readinitb(&rio, connfd);
    while ((n = Rio_readlineb(&rio, buf, MAXLINE)) != 0) {
        Rio_writen(connfd, buf, n);      /* 그대로 돌려보냄 */
    }
}
```

이 구조는 **iterative server** 입니다. 한 번에 한 클라이언트만 처리하므로 동시 접속을 지원하려면 fork·pthread·select·epoll 로 확장해야 합니다. 그 확장이 Concurrent Server 의 출발점입니다.

`Rio_readlineb` 는 개행까지 읽어 주는 버퍼드 I/O 이고, `Rio_writen` 은 원하는 길이를 다 쓸 때까지 반복해 주는 robust writer 입니다. 짧은 read·write 가 반환되더라도 전체 데이터가 전송되는 것을 보장합니다.

## 소켓에서 EOF 의 의미

네트워크 소켓은 파일 디스크립터와 같은 인터페이스(`read/write/close`) 로 다룹니다. 다만 EOF 의 의미가 미묘하게 다릅니다.

- 파일에서의 EOF — `read()` 가 0 을 반환한 순간, 파일 끝에 도달했습니다.
- 소켓에서의 EOF — `read()` 가 0 을 반환한 순간은 "상대가 자기 쪽 송신을 닫았다(FIN)" 는 의미입니다. 내 쪽 송신은 여전히 가능하며, 이 상태를 half-close 라 부릅니다.

```text
클라이언트                                서버
---------                                 ----
write(connfd, "hello", 5)                 read -> "hello"
                                          write("hello", 5)
read -> "hello"
close(clientfd)  -- FIN -->               read -> 0  (EOF)
                                          close(connfd)  -- FIN -->
read -> 0
```

에코 서버의 루프 조건이 `n != 0` 인 이유가 여기 있습니다. `n == 0` 이면 상대가 연결을 닫은 것이므로 루프를 빠져나와 `close(connfd)` 를 호출하고 다음 클라이언트를 받습니다.

## 파일 I/O 와 다른 세 가지

같은 디스크립터 인터페이스지만 네트워크에서 추가로 다뤄야 하는 상황이 셋 있습니다.

첫째, short read·short write 가 흔합니다. `write(1000)` 이 400 만 쓰고 돌아올 수 있습니다. 그래서 원하는 만큼 쓸 때까지 반복하는 `rio_writen` 래퍼가 필요합니다.

둘째, blocking 입니다. 읽을 데이터가 없으면 커널이 프로세스를 sleep 시킵니다. non-blocking 소켓이나 `select`·`poll`·`epoll` 로 대기를 제어합니다.

셋째, 에러 종류가 다양합니다. 파일에서는 대개 `EIO` 정도이지만 소켓에서는 `ECONNRESET`·`EPIPE`·`ETIMEDOUT` 같은 연결 상태 기반 에러가 많습니다. 특히 `EPIPE` 는 상대가 이미 FIN 을 보낸 뒤에 내가 write 한 경우에 발생하며 SIGPIPE 시그널도 함께 옵니다. 서버에서는 보통 `signal(SIGPIPE, SIG_IGN)` 으로 시그널을 무시하고 write 반환값의 errno 로 판단합니다.

## 요점

네트워크 I/O 는 파일 I/O 의 확장입니다. 같은 `read/write/close` 인터페이스를 쓰면서도 경계 보존 여부, EOF 의 half-close 의미, short read 대응, 연결 상태 에러를 함께 다뤄야 합니다. 에코 서버 한 편은 이 모든 차이를 압축해서 보여주는 학습용 뼈대이고, 여기에 동시성을 얹어 가는 것이 Concurrent Server 의 다음 주제입니다.
