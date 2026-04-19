# Pintos

<!-- description:start -->
PintOS 프로젝트 0~4. 가상화·스레드·사용자 프로그램·가상 메모리·파일 시스템.
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->
- [Project 0 PintOS](./Project%200%20PintOS/README.md) — 프로젝트 환경 설정과 자주 만나는 버그 패턴.
  - Virtual Machine Hypervisor
  - qemu
  - qemu Common bugs
  - Memory leak
  - Race condition
  - Deadlock
  - Use after free
- [Project 1 Threads](./Project%201%20Threads/README.md) — Time-sharing, 스케줄러, 동기화 프리미티브 구현.
  - Time-sharing system
  - Context Switching
  - Scheduler
  - Round Robin
  - Priority
  - Priority donation
  - MLFQS
  - 4BSD
  - nice
  - Thread
  - Thread control block
  - Timer Interrupt
  - Timer sleep
  - Synchronization
  - Semaphore
  - lock
  - condvar
- [Project 2 User Programs](./Project%202%20User%20Programs/README.md) — 유저/커널 모드, 프로세스, 시스템콜, ELF 로더.
  - User mode vs Kernel mode
  - Process
  - Process Environment block
  - Process identifier
  - User Stack
  - x86_64 calling convention
  - Register vs Memory
  - argument vector
  - ELF loader
  - system call
  - filesys syscall
  - process syscall
  - file descriptor
  - file descriptor table
  - dup2 syscall
  - 사용자 포인터 검증
  - multi-oom
- [Project 3 Virtual Memory](./Project%203%20Virtual%20Memory/README.md) — 가상 메모리 관리, 페이지 타입, 스왑, COW.
  - Virtual memory management
  - paging
  - virtual page
  - physical frame
  - page table
  - supplementary page table
  - MMU
  - TLB
  - Uninitialized page
  - Lazy initialization
  - Anonymous page
  - stack growth
  - file-backed page
  - mmap syscall
  - Swap in out
  - page replacement policy
  - swap disk
  - Copy on Write
- [Project 4 File System](./Project%204%20File%20System/README.md) — 파일 시스템 구성 요소와 구현, 저널링.
  - FAT
  - Berkley FFS
  - EXT
  - file
  - extensible file
  - directory
  - working directory
  - hard link vs soft link
  - sector cluster
  - super block
  - disk inode
  - in-memory inode
  - open inode table
  - Buffer cache
  - filesystem mount
  - Journaling
<!-- tree:end -->
