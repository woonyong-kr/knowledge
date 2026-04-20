---
title: fd 수명과 디스패치 — close·CLOEXEC·proto 콜백·공유·버퍼링
category: 네트워크
keyword: 소켓 내부 구조
subkeyword: fd 생명주기
created: 2026-04-20
updated: 2026-04-20
tags: [close, cloexec, struct-file, f-op, strategy-pattern, dup2, stdio-buffering, everything-is-a-file]
summary: close 는 객체를 죽이는 것이 아니라 참조 하나를 버리는 것입니다. fd 가 가리키는 struct file 의 refcount, execve 경계의 CLOEXEC, TCP·UDP close 가 같은 함수에서 다르게 움직이는 strategy pattern, dup2 리다이렉트, libc 버퍼링까지 fd 의 생애 전체를 정리합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q20-fd-lifecycle-and-dispatch.md
---

# fd 수명과 디스패치 — close·CLOEXEC·proto 콜백·공유·버퍼링

fd 는 "이 프로세스가 어떤 커널 객체를 참조한다" 는 핸들입니다. 번호·객체·수명이 따로 관리되고, 같은 시스템콜 `close` 가 TCP 에서는 60 초를 걸리고 UDP 에서는 즉시 끝나는 이유가 모두 이 분리된 설계에서 나옵니다.

## close 는 참조 하나를 버리는 연산이다

가장 중요한 오해부터 정정해야 합니다. `close(fd)` 는 객체를 죽이지 않습니다. **슬롯을 비우고 `struct file` 의 refcount 를 하나 감소**시킬 뿐이고, 객체 해제는 refcount 가 0 이 될 때만 일어납니다.

```text
층 A  fdtable 슬롯         task 당 하나, 가벼움
층 B  struct file          전역, f_op·refcount·f_pos 보유
층 C  struct inode / sock  파일/소켓 그 자체
```

커널 코드 `close_fd()` 의 골격은 다음과 같습니다.

```c
int close_fd(unsigned fd) {
    /* 1) 슬롯 비우기 (RCU 로 publish) */
    rcu_assign_pointer(fdt->fd[fd], NULL);
    __clear_bit(fd, fdt->open_fds);
    __clear_bit(fd, fdt->close_on_exec);

    /* 2) struct file 의 refcount 감소. 0 이면 __fput 지연 실행 */
    return filp_close(file, files);
}
```

`filp_close → fput → __fput → file->f_op->release` 체인에서 실제 해제가 일어납니다. fork 후 부모·자식이 모두 close 해야 비로소 `struct file` 이 사라지며, 이 두 수명은 독립적입니다.

## O_CLOEXEC 는 execve 경계에서만 작동한다

흔한 오해: "CLOEXEC 로 열면 자식이 fd 에 접근할 때 커널이 막아준다." 사실은 "execve 순간에만 닫히고, 그 전까지는 자식이 자유롭게 쓴다" 입니다.

```text
Parent: open("a.txt", O_RDONLY | O_CLOEXEC)  -> fd=3
Parent: fork()
  ├ Parent 계속 사용
  └ Child  fdtable 복제. fd=3, close_on_exec=1
           Child read(3, ...) -> 됨 (아직 exec 안 함)
           Child execve("/bin/ls") -> 이 순간 커널이 fd 3 을 close
                                     Parent 의 fd 3 은 영향 없음
```

주의할 점은 CLOEXEC 가 **fd 의 속성** 이지 **`struct file` 의 속성** 이 아니라는 것입니다. 같은 `struct file` 을 가리키는 두 fd 중 한쪽만 CLOEXEC 를 가질 수 있습니다. 보안상의 대표 용도는 비밀 파일이 CGI 같은 자식에게 샐 위험을 막는 것입니다.

## "파일과 소켓이 같다" 의 정확한 의미

유닉스의 "everything is a file" 은 인터페이스 시그니처가 같다는 뜻이지 구현이 같다는 뜻이 아닙니다. 실제로는 모든 fd 가 `struct file` 이라는 공통 관문을 거치고, 그 안의 `f_op` 함수 포인터 테이블로 구현이 분기됩니다.

```c
struct file {
    const struct file_operations *f_op;   /* read/write/release/poll/... */
    atomic_long_t                 f_count;
    fmode_t                       f_mode;
    loff_t                        f_pos;
    void                         *private_data;
    ...
};
```

| fd 타입 | f_op | read 구현 | close 체인 |
|---|---|---|---|
| regular file | `ext4_file_operations` | `ext4_file_read_iter` | `ext4_release_file` |
| pipe | `pipefifo_fops` | `pipe_read` | `pipe_release` |
| socket | `socket_file_ops` | `sock_read_iter` | `sock_close` |
| tty | `tty_fops` | `tty_read` | `tty_release` |
| eventfd | `eventfd_fops` | `eventfd_read` | `eventfd_release` |
| epoll | `eventpoll_fops` | — | `ep_eventpoll_release` |

시스템콜 `sys_read` 는 fd 가 무엇인지 절대 몰라야 한다는 것이 VFS 설계의 핵심입니다.

## TCP 와 UDP 의 close — 4 단계 strategy pattern

같은 `close(fd)` 가 TCP 에서는 FIN·ACK·TIME_WAIT 60 초를 걸고, UDP 에서는 버퍼만 비우고 끝납니다. 이 차이는 소켓 close 가 4 단계 함수 포인터 디스패치로 구현돼 있기 때문입니다.

```text
close(fd)
  └ filp_close → fput → __fput → file->f_op->release  [VFS 공통 = sock_close]
      └ sock->ops->release                             [프로토콜 패밀리 = inet_release]
          └ sk->sk_prot->close                          [프로토콜 = tcp_close / udp_lib_close]
```

| 단계 | 필드 | TCP | UDP |
|---|---|---|---|
| VFS | `file->f_op` | `sock_close` | `sock_close` |
| 패밀리 | `sock->ops` | `inet_release` | `inet_release` |
| 프로토콜 | `sk->sk_prot->close` | `tcp_close` | `udp_lib_close` |
| 동작 | — | FIN → FIN_WAIT → TIME_WAIT 60s | 수신 큐 비우고 즉시 해제 |

`tcp_prot`·`udp_prot` 구조체가 각자의 `close` 를 등록해 두면 `inet_release` 는 어떤 프로토콜인지 몰라도 동일한 경로로 호출할 수 있습니다. 신뢰 프로토콜과 비신뢰 프로토콜의 상이한 종료 절차를 상위 계층은 모르게 숨기는 strategy pattern 의 교과서적 사례입니다. TIME_WAIT 슬롯은 프로세스가 죽어도 커널에 남으며 `ss -tan | grep TIME-WAIT` 로 확인할 수 있습니다.

## 공유된 fd 의 동시 사용 — 경쟁적 소비/출력

fork 이후 부모·자식은 `fdtable` 은 다르지만 같은 `struct file` 을 공유합니다.

공유되는 것은 `f_pos`·`f_flags`·수신·송신 큐·inode 참조이고, 공유되지 않는 것은 fd 번호 자체와 `close_on_exec` 비트입니다.

```text
Parent read(3, buf1, 10)  -> 0~9, f_pos=10
Child  read(3, buf2, 10)  -> 10~19, f_pos=20
Parent read(3, buf3, 10)  -> 20~29, f_pos=30
```

같은 파일을 두 프로세스가 순차 read 하면 내용이 나뉘어 소비됩니다("destructive consumption"). 키보드 TTY 도 동일합니다. `'A'` 한 글자를 입력하면 두 프로세스 중 하나만 깨어나서 가져갑니다. 반대로 write 는 **누적**입니다. 둘 다 출력이 나가지만 PIPE_BUF (보통 4096B) 를 넘는 write 는 문자열이 섞일 수 있습니다.

prefork 웹 서버가 같은 listen socket 을 여러 자식이 `accept` 하는 것도 이 공유 메커니즘을 활용한 것입니다. 커널은 thundering herd 를 피하기 위해 연결 하나에 자식 하나만 깨웁니다.

## fd 로 접근 가능한 객체 지도

"파일·디렉토리·소켓·파이프" 네 가지로 알려져 있지만 실제는 훨씬 넓습니다. 커널이 새 기능을 추가할 때도 fd 추상화에 맞춰 올려 두는 경향이 강해지고 있습니다.

| 카테고리 | 대표 fd 종류 |
|---|---|
| 파일시스템 | regular file, directory, symlink (O_PATH), FIFO |
| IPC | anonymous pipe, UNIX socket (stream/dgram/seqpacket) |
| 네트워크 | TCP, UDP, RAW, PACKET, NETLINK |
| TTY | 물리 TTY, PTY (`/dev/ptmx` + `/dev/pts/N`) |
| 디바이스 | char device (`/dev/null`·`/dev/urandom`), block device |
| 이벤트 | eventfd, timerfd, signalfd, inotify, fanotify, pidfd |
| 멀티플렉싱 | epoll, io_uring |
| 메모리·격리 | memfd, userfaultfd, perf_event, bpf fd |
| 네임스페이스 | `/proc/PID/ns/*`, cgroup fd |
| 메타 | `O_PATH` fd, `/proc/self/fd/N` |
| 특수 | DRM fd, dmabuf fd |

"같은 호스트 두 프로세스 간 바이트 스트림" 은 pipe 또는 UNIX stream socket, "파일 변경 감시" 는 inotify, "시그널을 동기적으로 받기" 는 signalfd 식으로 매핑해 두면 고를 때 편합니다.

## stdin·stdout·stderr 는 커널이 구분하지 않는다

오해: "커널이 fd 0·1·2 를 특별히 취급한다." 사실은 "커널은 번호를 보지 않고 `struct file->f_mode` 의 `FMODE_READ`·`FMODE_WRITE` 만 본다" 입니다. 0·1·2 는 libc 매크로와 셸의 관행이 유지하는 약속입니다.

```c
#define STDIN_FILENO   0
#define STDOUT_FILENO  1
#define STDERR_FILENO  2
```

fd 0 이 `O_RDWR` 로 열린 TTY 라면 `write(0, ...)` 도 가능합니다. stdout 과 stderr 의 차이는 커널 차원에서는 없고, libc 차원에서 stdout 은 line/block-buffered 이고 stderr 는 unbuffered 라는 버퍼링 정책만 다릅니다.

## dup2 리다이렉트 — 셸·CGI·inetd 의 공통 무기

`dup2(oldfd, newfd)` 는 "newfd 슬롯이 oldfd 와 같은 `struct file` 을 가리키게 만든다" 는 의미입니다. 이 때 newfd 가 이미 열려 있으면 내부적으로 close 를 먼저 하고, `struct file` 의 refcount 가 하나 증가합니다.

```c
/* bash 의 "./prog > out.txt" 구현 요지 */
if ((pid = fork()) == 0) {
    int f = open("out.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    dup2(f, 1);
    close(f);
    execve("./prog", argv, envp);
}
```

인접 패턴이 두 가지 더 있습니다. 파이프라인 `cmd1 | cmd2` 는 pipe fd 를 각각 `dup2(w, 1)` 와 `dup2(r, 0)` 으로 꽂아 구현합니다. inetd·CGI 는 accept 한 소켓을 `dup2(conn, 0)`·`dup2(conn, 1)`·`dup2(conn, 2)` 로 꽂아서 외부 프로그램이 소켓 API 를 전혀 몰라도 `scanf`·`printf` 만으로 네트워크 데몬이 되게 합니다. 초기 유닉스의 "CLI 도구를 그대로 네트워크화" 라는 철학이 여기서 나옵니다.

`dup2` 가 필요한 이유는 execve 이후 프로그램이 fd 0·1·2 를 약속으로 찾기 때문입니다. `close` 만 해서는 `open` 이 재사용해 줄 번호를 보장하지 못해 원자적인 번호 고정이 필수입니다.

## libc stdio 의 2-레벨 버퍼링

"stdout 이 line-buffered" 같은 표현은 커널이 아니라 libc `FILE*` 이야기입니다. 구조는 2 단계입니다.

```text
printf("hi\n")       → libc FILE* 버퍼 누적                (syscall 없음)
fflush(stdout)       → write(1, buf, n) 시스템콜            (커널 버퍼 진입)
fsync(1)             → 커널 버퍼 → 디스크                    (FS 에서만 유효)
```

버퍼 모드는 셋입니다. `unbuffered` 는 쓰는 즉시 write 를 호출하며 stderr 기본값입니다. `line-buffered` 는 `\n` 이 나오거나 버퍼가 찰 때 flush 하며 TTY 에 연결된 stdout 기본값입니다. `block-buffered` 는 버퍼 (BUFSIZ=8192) 가 찰 때만 flush 하며 파이프·파일에 연결된 stdout 기본값입니다.

실무의 함정은 `./prog | cat` 처럼 파이프에 넘기면 stdout 이 block-buffered 로 바뀌어 `printf("progress...")` 가 한참 뒤에야 보이는 현상입니다. 대응은 `fflush(stdout)` 명시 호출이나 `setvbuf(stdout, NULL, _IOLBF, 0)` 로 모드를 강제하는 것입니다.

`fflush` 가 하는 일과 `fsync` 가 하는 일을 구분해야 합니다. `fflush` 는 libc 버퍼를 커널로 보내는 `write()` 이고, `fsync` 는 커널 페이지 캐시를 물리 디스크에 내리는 블록 장치 호출입니다. "왜 안 찍히느냐" 의 답은 대개 libc 버퍼링 미flush 이고, "왜 디스크에 없느냐" 의 답은 대개 fsync 누락입니다.

## 한 장의 다이어그램

```text
int fd = open("a.txt", O_RDONLY | O_CLOEXEC);
  ├ do_sys_open
  │   ├ struct file 할당, f_op = ext4_file_operations
  │   ├ inode 참조++, fdtable 빈 슬롯 = 3
  │   └ fdtable[3] = file, close_on_exec bit[3] = 1
read(fd, buf, 4096)
  └ vfs_read → file->f_op->read_iter → page cache / 디스크 → copy_to_user
fork()
  └ copy_files: fdtable 복제, struct file f_count++
Child execve("/bin/ls")
  └ do_close_on_exec: fdtable[3] = NULL, f_count--
Parent close(fd)
  └ sys_close → close_fd → filp_close → fput (f_count 0) → __fput
                → file->f_op->release → inode 참조-- → struct file free
```

## 체크리스트

- `close(fd)` 는 참조 반납이고 `struct file` 해제는 refcount 0 이 될 때 일어난다는 사실을 기억한다
- `O_CLOEXEC` 는 execve 경계에서만 작동하며, 자식이 exec 전에는 여전히 fd 를 쓸 수 있다
- 시스템콜 경로가 같더라도 `file->f_op` 가 분기시키는 구현이 모든 fd 타입별로 다르다
- TCP·UDP 의 close 차이는 `sk_prot->close` 가 등록하는 함수가 다를 뿐 상위 계층은 동일하다
- fork 후 공유된 fd 는 `f_pos`·수신 큐·송신 큐를 함께 사용하므로 read 는 경쟁적 소비, write 는 누적 출력이다
- stdin/stdout/stderr 는 커널이 구분하지 않으며 `dup2` 로 얼마든지 다른 객체로 갈아끼울 수 있다
- "왜 안 찍혀?" 의 답은 십중팔구 libc 버퍼링 미flush 이고, fsync 와 fflush 의 책임 범위는 다르다

## 요점

fd 의 생애는 세 개의 층으로 분리돼 있습니다. fdtable 슬롯 (프로세스당), `struct file` (전역·refcount 기반), 실제 객체 (inode·socket 등). close·CLOEXEC·dup2·fork 가 각각 어느 층에 작용하는지를 구분하면 TCP 의 느린 close·CGI 의 소켓-stdin 매핑·libc 버퍼링 문제까지 하나의 모델로 설명됩니다. fd 추상화는 커널이 "모든 리소스를 프로세스가 참조하는 단일 방식" 으로 계속 확장하고 있는, 유닉스 설계의 가장 강력한 유산입니다.
