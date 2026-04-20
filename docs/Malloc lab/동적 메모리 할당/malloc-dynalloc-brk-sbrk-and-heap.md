---
title: brk·sbrk 와 힙 영역의 확장 — 경계를 움직여 메모리를 늘리는 법
category: Malloc lab
keyword: 동적 메모리 할당
created: 2026-04-20
updated: 2026-04-20
tags: [brk, sbrk, heap, vma, malloc, mmap]
summary: 커널이 힙 영역을 관리하는 방식은 "program break 라는 경계 값 하나" 입니다. brk·sbrk 가 그 경계를 움직이고, 그 위에 malloc 이 자기 자료구조를 세웁니다.
source: _krafton/SW_AI-W07-SQL/docs/blog/concepts/15-brk-sbrk-and-heap.md
---

# brk·sbrk 와 힙 영역의 확장 — 경계를 움직여 메모리를 늘리는 법

프로세스의 힙(Heap) 은 동적 할당을 위한 영역입니다. 공부하며 흥미로웠던 부분은, 커널에게 "힙" 이라는 자료구조 자체가 없다는 사실이었습니다.

커널은 단지 데이터 영역 바로 위에 있는 한 경계 — program break — 의 값을 유지할 뿐입니다. 이 값을 위로 밀면 힙이 커지고, 아래로 당기면 줄어듭니다. 그 값을 움직이는 시스템 콜이 `brk` 와 `sbrk` 입니다.

## 힙이란 무엇인가

힙은 BSS 바로 위 가상 주소에서 시작해 `mm_struct->start_brk` 부터 `mm_struct->brk` 까지 이어지는 단일 VMA 입니다. 이 VMA 의 권한은 `rw-` 이고, `vm_file` 은 `NULL` (익명 매핑) 입니다.

```
  ┌──────────────────────────────┐
  │           ...                 │
  ├──────────────────────────────┤  ← mm_struct->brk  (움직이는 경계)
  │         Heap VMA              │
  │  (rw-, anonymous)             │
  ├──────────────────────────────┤  ← mm_struct->start_brk
  │           BSS                 │
  │           Data                │
  │           Text                │
  └──────────────────────────────┘
```

`brk` 가 `start_brk` 와 같은 상태에서는 힙의 크기가 0 입니다. `brk` 를 위로 밀면 그만큼 힙 VMA 의 크기가 늘어나고, 새로 생긴 가상 주소를 프로세스에 쓸 수 있게 됩니다.

## brk 와 sbrk 의 시그니처

```c
int   brk(void *addr);        // break 를 addr 로 설정
void *sbrk(intptr_t incr);    // break 를 incr 만큼 이동, 이전 값 반환
```

- `brk(addr)` — break 를 `addr` 로 설정합니다. 성공 시 0, 실패 시 -1 을 반환합니다.
- `sbrk(incr)` — break 를 `incr` 바이트만큼 이동합니다. 양수는 확장, 음수는 축소, 0 은 현재 break 조회를 의미합니다. 반환값은 이전 break 값입니다. 즉 `sbrk(0)` 은 "지금 break 가 어디 있는가" 를 묻는 관용구입니다.

두 호출은 커널 내부에서 본질적으로 `mm_struct->brk` 를 움직이는 연산입니다. 경계가 위로 움직이면 힙 VMA 가 확장되고, 아래로 움직이면 축소됩니다.

확장된 페이지들은 요구 페이징으로 처리됩니다. VMA 만 커질 뿐, 실제 물리 프레임은 처음 접근 시 0 으로 채워진 프레임이 배정됩니다.

## 힙 확장 과정

```mermaid
sequenceDiagram
    participant App
    participant Libc as glibc malloc
    participant K as Kernel
    participant PT as 페이지 테이블
    App->>Libc: malloc(1KB)
    Libc->>K: brk(현재_break + 4KB)
    K->>K: 힙 VMA 끝을 +4KB 확장
    K-->>Libc: 성공
    Libc-->>App: payload 포인터 반환
    App->>App: *p = 1; (첫 접근)
    App->>PT: 가상 주소 접근 → PTE.P=0
    PT->>K: Page Fault
    K->>K: 0 으로 채운 프레임 할당, PTE 업데이트
    K-->>App: 명령 재실행 (쓰기 성공)
```

`brk` 로 받은 메모리는 커널 입장에서는 4 KB 단위로 늘어나는 VMA 영역이고, glibc `malloc` 입장에서는 자신이 관리할 전체 풀입니다.

`malloc` 은 한 번의 `brk` 로 큰 덩어리를 받아 내부 자료구조로 쪼개어 관리합니다.

## 힙 = brk 공간, malloc = 할당기

처음에는 이 구분이 헷갈렸는데, 명확히 정리하면 다음과 같습니다.

힙은 주소 공간의 한 영역이고, `malloc` 은 그 영역을 조각내 사용자에게 나눠 주는 할당기입니다. 두 역할은 다릅니다.

- 커널 — 힙의 경계(break) 만 관리합니다. 경계 안쪽이 어떻게 쪼개져 쓰이는지는 모릅니다.
- glibc (`malloc`/`free`) — break 안쪽을 블록(header + payload + footer) 으로 쪼개고, free 리스트를 관리합니다.

그래서 `malloc` 은 `brk` 를 직접 부르지 않습니다. 내부적으로 필요한 만큼만 호출합니다. 작은 할당을 받을 때마다 시스템 콜을 부르면 성능이 망가지므로, 한 번의 `brk` 로 크게 확장한 뒤 내부 자료구조에서 잘라 씁니다.

## brk 의 한계 — 왜 큰 할당은 mmap 으로 가는가

`brk` 로만 힙을 관리하면 두 가지 한계에 부딪힙니다.

첫째, 반환의 어려움입니다. 힙은 단일 연속 VMA 이므로 중간에 큰 free 블록이 있어도 `brk` 를 아래로 당기려면 상단의 모든 블록이 free 상태여야 합니다. 한 블록만 상단 근처에 살아 있어도 그 아래 수십 MB 를 돌려줄 수 없습니다.

```
 brk ──▶ | living block |                ← 이것 때문에
         |   free 50MB   |                   brk 를 당길 수 없음
         |   free 20MB   |
 start_brk ─▶
```

둘째, 스레드 경합입니다. `brk` 는 프로세스 전체의 단일 경계이므로 여러 스레드가 동시에 `malloc` 할 때 잠금이 필요합니다.

그래서 glibc 의 `malloc` 은 큰 할당(기본 128 KB 이상) 에 대해 `brk` 대신 anonymous private `mmap` 을 사용합니다. `mmap` 으로 받은 영역은 개별 VMA 이므로 `free` 시점에 `munmap` 으로 통째로 반환할 수 있습니다. 힙 단편화의 상단 문제를 우회하는 방법입니다.

## sbrk(0) 로 break 위치 확인하기

```c
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
int main(void) {
    printf("initial break: %p\n", sbrk(0));
    void *p = malloc(1024);
    printf("after malloc(1KB): %p\n", sbrk(0));
    free(p);
    printf("after free:        %p\n", sbrk(0));

    void *big = malloc(1 * 1024 * 1024); // 1MB
    printf("after malloc(1MB): %p\n", sbrk(0));
    free(big);
    printf("after free(1MB):   %p\n", sbrk(0));
    return 0;
}
```

첫 `malloc(1KB)` 이후 break 는 수 KB 또는 수십 KB 증가할 수 있습니다. `malloc` 이 여유 있게 한 번에 확장하기 때문입니다. `free` 후에도 대체로 break 는 원위치로 돌아오지 않고, 블록은 free list 에 들어갈 뿐입니다. 큰 할당(1 MB) 은 `mmap` 경로로 가므로 break 에 변화가 없을 수 있습니다. 이 한 번의 실험으로 glibc `malloc` 의 전략을 대략 엿볼 수 있습니다.

## brk 가 실패할 때

`brk(addr)` 가 실패하는 주된 원인은 다음과 같습니다.

- 주소 공간 자체가 부족 — `brk` 가 다른 VMA(예: 공유 라이브러리 매핑) 와 충돌.
- `RLIMIT_DATA` 같은 자원 한도 초과.
- 시스템 전체의 물리 메모리·스왑 고갈 (요청이 너무 크면).

실패 시 `brk` 는 -1 을, `sbrk` 는 `(void *) -1` 을 반환합니다. 이 경우 `malloc` 은 `mmap` 경로로 전환하거나 `NULL` 을 반환합니다.

## 정리

`brk` 와 `sbrk` 는 단 하나의 값 — program break — 을 움직이는 가장 단순한 메모리 시스템 콜입니다.

그런데 그 한 값이 힙 VMA 의 상단을 정의하고, 그 영역 위에 `malloc` 이 자기 자료구조를 세웁니다. 커널은 경계만 알고, 할당기는 경계 안을 쪼개는 역할 분담이, 유저 공간의 편의로 "힙" 이라는 추상을 성립시킵니다. 동시에 `brk` 의 한계(반환의 어려움) 가 큰 할당을 `mmap` 으로 이전하게 만드는 동력이 됩니다.
