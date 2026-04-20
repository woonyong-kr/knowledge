# 소켓 내부 구조

<!-- description:start -->
struct socket·sk_buff·sockfs·fd→socket 포인터 체인·sk_receive_queue.
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->
- [fd 생명주기](./fd%20%EC%83%9D%EB%AA%85%EC%A3%BC%EA%B8%B0/README.md) — 파일 디스크립터 생성·복제·종료·dispatch 의 전체 흐름.
- [struct socket 과 sk_buff](./struct%20socket%20%EA%B3%BC%20sk_buff/README.md) — 커널 소켓 구조체와 네트워크 버퍼의 관계.
- [sockfs 와 fd to socket 체인](./sockfs%20%EC%99%80%20fd%20to%20socket%20%EC%B2%B4%EC%9D%B8/README.md) — fd→file→socket 포인터 경로와 sockfs 역할.
- [소켓 버퍼 큐](./%EC%86%8C%EC%BC%93%20%EB%B2%84%ED%8D%BC%20%ED%81%90/README.md) — sk_receive_queue·sk_write_queue 의 구조와 소비 흐름.
<!-- tree:end -->

## 포스트

<!-- posts:start -->
(없음)
<!-- posts:end -->
