---
title: 프로세스의 조상과 fd 상속 — PID 0·1·2 와 CLOEXEC·setsid
category: 네트워크
keyword: 소켓 내부 구조
subkeyword: fd 생명주기
created: 2026-04-20
updated: 2026-04-20
tags: [init, fork, cloexec, setsid, daemonize, systemd, fdtable, controlling-tty]
summary: 모든 프로세스가 fork 의 자손이라면 "맨 처음" 부모는 누구이며, fork 가 fdtable 을 복제한다는데 왜 어떤 서비스는 터미널과 분리돼 있는지 풀어냅니다. PID 0/1/2 의 부팅 기원, O_CLOEXEC·close·setsid·double-fork 로 상속을 끊는 네 방법을 정리합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q19-process-ancestry-fd-inheritance.md
---

# 프로세스의 조상과 fd 상속 — PID 0·1·2 와 CLOEXEC·setsid

"모든 프로세스는 fork 로 만들어진다"는 설명에는 두 가지 후속 질문이 따릅니다. 그 포크의 맨 처음 부모는 누구이며, fdtable 이 복제된다면 왜 systemd 가 띄운 서비스는 터미널에 출력이 뜨지 않을까요. 답은 "커널이 직접 만든 PID 0·1·2 가 베이스 케이스이고, 자식이 상속받은 fd 를 스스로 버리는 도구가 따로 있다" 는 것입니다.

## fork 의 베이스 케이스 — PID 0·1·2

유저 프로세스의 조상은 `/sbin/init` (systemd) 이지만 그 앞에는 커널이 부팅 중에 `kzalloc` 으로 직접 `task_struct` 를 조립한 프로세스 셋이 있습니다.

| PID | 이름 | 만드는 방식 | 역할 |
|---|---|---|---|
| 0 | swapper/idle | `start_kernel` 이 직접 구성 | CPU 당 한 개의 idle 프로세스 |
| 1 | init/systemd | `kernel_thread(kernel_init,...)` 후 `execve("/sbin/init")` | 모든 유저 프로세스의 조상 |
| 2 | kthreadd | `kernel_thread(kthreadd,...)` | 이후 모든 커널 스레드의 부모 |

fork 는 기존 `task_struct` 를 복사하는 연산이므로 최소 하나가 "없는 상태에서" 만들어져야 재귀가 시작됩니다. `init/main.c` 의 `start_kernel → rest_init` 이 그 지점입니다.

```c
static noinline void __ref rest_init(void) {
    rcu_scheduler_starting();
    kernel_thread(kernel_init, NULL, CLONE_FS);        /* PID 1 */
    kernel_thread(kthreadd,   NULL, CLONE_FS|CLONE_FILES); /* PID 2 */
    cpu_startup_entry(CPUHP_ONLINE);                   /* PID 0 idle */
}
```

`kernel_init` 이 파일시스템 마운트를 끝내면 `execve("/sbin/init")` 로 유저 프로그램으로 변신합니다. `execve` 는 동일한 `task_struct` 를 유지한 채 코드만 교체하므로 PID 1 은 그대로이며 이후 유저 공간의 모든 프로세스가 PID 1 의 후손이 됩니다.

## fork 의 fd 복제 — 같은 struct file 을 가리키는 두 개의 fdtable

`fork()` 는 내부적으로 `clone → _do_fork → copy_process` 를 거치고 fd 와 관련된 작업은 `copy_files` 가 담당합니다. `CLONE_FILES` 플래그가 없으면 `dup_fd` 로 `fdtable` 을 새로 만들되, 각 슬롯은 부모와 같은 `struct file` 을 가리키고 참조 카운트만 증가합니다.

```text
부모 fdtable                          자식 fdtable
 [0]─┐                                 [0]─┐
 [1]─┼── 같은 struct file              [1]─┼── 같은 struct file
 [2]─┤     (f_count 가 2 로 증가)      [2]─┤
 [3]─┘                                 [3]─┘
```

결과적으로 fd 번호는 같지만 양쪽이 같은 `struct file` 을 공유하므로 파일 오프셋·수신 큐·플래그까지 함께 움직입니다. stdin/stdout/stderr 도 당연히 공유됩니다. "어떤 서비스는 터미널에 출력이 안 뜬다" 는 현상은 자식이 받은 fd 를 스스로 버린 결과입니다.

## 상속을 끊는 네 가지 도구

### O_CLOEXEC — 열 때부터 "execve 시 닫으라"고 표시

가장 보편적이고 안전한 방법입니다. 플래그는 `fdtable` 의 `close_on_exec` 비트맵에 저장되며 `execve` 순간 커널이 `do_close_on_exec` 로 일괄 처리합니다.

```c
int fd = open("/etc/server.key", O_RDONLY | O_CLOEXEC);
/* fork 해도 자식은 fd 3 을 받지만, execve 순간 커널이 자동 close.
   execve 전에 자식이 read(3) 하는 건 막지 않습니다. */
```

libc 2.7+ 의 `fopen(path, "re")` 가 이 플래그를 붙여 주고, `SOCK_CLOEXEC`·`pipe2(..., O_CLOEXEC)` 로 소켓·파이프에도 붙일 수 있습니다. 현대 리눅스의 베스트 프랙티스는 새 fd 를 기본적으로 CLOEXEC 로 여는 것입니다.

### 명시적 close — execve 직전 훑어내기

```c
if ((pid = fork()) == 0) {
    close(3); close(4); close(5);
    execve("/usr/bin/myprog", argv, envp);
}
```

간단하지만 열린 fd 가 늘면 누락이 생깁니다. 방어 코드로 `/proc/self/fd` 를 순회하며 3 이상을 전부 닫는 패턴을 함께 씁니다.

### posix_spawn + file_actions — 선언적 리다이렉트

```c
posix_spawn_file_actions_t fa;
posix_spawn_file_actions_init(&fa);
posix_spawn_file_actions_addclose(&fa, 3);
posix_spawn_file_actions_adddup2(&fa, logfd, 1);
posix_spawn(&pid, "/usr/bin/myprog", &fa, NULL, argv, envp);
```

systemd 가 서비스를 띄울 때 내부적으로 쓰는 방식입니다. `fork+exec` 사이 상태를 선언형으로 지정할 수 있어 누락이 줄어듭니다.

### setsid 와 컨트롤링 TTY 분리

fd 를 갖고 있는 것과 "터미널에 붙어 있는" 것은 다른 문제입니다. 컨트롤링 TTY 는 fd 차원이 아니라 **세션** 차원의 속성입니다.

```text
Session ─┬── Process Group ─┬── Process ─── Thread
         │                  │
         └── 최대 한 개의     └── 하나의 job
             컨트롤링 TTY         (포그라운드 pgid 만
             (Ctrl+C, SIGHUP)      SIGINT 수신)
```

`setsid()` 는 세 가지를 동시에 수행합니다. 새 세션의 리더로 등록하고, 기존 컨트롤링 TTY 와의 연결을 끊고, 새 프로세스 그룹을 만듭니다. 단, 이미 세션 리더면 실패합니다.

## 데몬화 — double-fork + setsid 의 이유

전통적 SysV 데몬은 아래 순서를 밟습니다.

```c
void daemonize(void) {
    if (fork() > 0) exit(0);            /* (1) 부모 종료 — 자식은 orphan, PID 1 이 입양 */
    if (setsid() < 0) exit(1);          /* (2) 새 세션·pgid·TTY 분리 */
    if (fork() > 0) exit(0);            /* (3) 세션 리더 아닌 자식으로 재탄생 */
    chdir("/"); umask(0);               /* (4) 언마운트·상속 umask 차단 */
    int fd = open("/dev/null", O_RDWR); /* (5) 표준 fd 리다이렉트 */
    dup2(fd, 0); dup2(fd, 1); dup2(fd, 2);
    if (fd > 2) close(fd);
}
```

두 번 fork 하는 이유는 (2) 직후의 자식이 세션 리더이기 때문입니다. 세션 리더는 조건만 맞으면 `open("/dev/tty", O_RDWR)` 로 TTY 를 다시 잡을 수 있어, 이를 영구 차단하려면 리더가 아닌 손자를 한 단계 더 만들어야 합니다.

| 단계 | 세션 | 세션리더 | TTY 재획득 |
|---|---|---|---|
| 원본 bash | 3000 | yes | 이미 가짐 |
| 1차 fork | 3000 | no | yes |
| `setsid` | 4000 | yes | no |
| 2차 fork | 4000 | no | no (영구) |

## systemd 의 다른 선택 — double-fork 를 버리다

현대 리눅스에서는 `systemd` 가 직접 부모가 되어 cgroup·네임스페이스·stdin/out/err redirection·환경변수를 `posix_spawn` 스타일로 설정합니다. 서비스는 그냥 실행만 하면 됩니다.

```text
[systemd]
  ├─ cgroup 생성
  ├─ O_CLOEXEC 로 fd 정리
  ├─ setsid
  └─ execve
[서비스]  stdin=/dev/null, stdout/stderr → journald 파이프
```

`systemctl start foo.service` 가 터미널에 출력을 뿌리지 않는 이유가 여기 있습니다. 서비스의 stdout/stderr 가 TTY 대신 journald 의 소켓으로 연결되어 있고, 로그는 `journalctl -u foo.service` 로 확인합니다.

## 도구별 비교

| 도구 | TTY 분리 | fd 처리 | 특징 |
|---|---|---|---|
| `./prog` | 안 함 | 상속 | Ctrl+C 로 종료 가능 |
| `./prog &` | 안 함 | 상속 | 포그라운드 pgid 아님, 쉘 종료 시 SIGHUP |
| `nohup ./prog &` | 반쯤 | stdin=`/dev/null`, stdout=`nohup.out` | SIGHUP 무시 |
| `setsid ./prog` | 함 | 상속 | 새 세션, TTY 완전 분리 |
| `systemd-run ./prog` | 함 | journald | cgroup 에 넣어 관리 |
| `daemon(3)` | 함 | `/dev/null` | 라이브러리가 double-fork 수행 |

## 체크리스트

- 모든 유저 프로세스가 PID 1 의 자손이라는 사실과, PID 0·1·2 가 `start_kernel` 에서 직접 만들어지는 예외라는 사실을 구분한다
- fork 후 자식이 받는 것은 "같은 `struct file` 을 가리키는 fdtable" 이며 `f_pos` 와 수신 큐까지 공유된다
- 새로 여는 fd 에는 기본적으로 `O_CLOEXEC` 를 붙여 exec 경계에서 자동 close 되도록 한다
- 데몬화는 fd 리다이렉트만으로 부족하다. 컨트롤링 TTY 분리를 위해 `setsid` 가 필요하며, 재획득을 막으려 double-fork 한다
- systemd 환경에서는 double-fork 대신 unit 파일의 `Type=simple` 로 맡기는 것이 깔끔하다

## 요점

fork 의 재귀는 PID 1 에서 멈추고, PID 1 이전의 조상은 커널이 부팅 중 조립합니다. fdtable 은 기본 복제이므로 자식은 부모의 모든 fd 를 가진 채 태어나며, 이 상속을 끊는 도구는 `O_CLOEXEC`·명시적 close·`posix_spawn`·`setsid` 네 가지입니다. "터미널 분리" 는 fd 가 아니라 세션 차원의 일이며, 현대 리눅스는 대부분 systemd 에게 이 모든 조합을 위임합니다.
