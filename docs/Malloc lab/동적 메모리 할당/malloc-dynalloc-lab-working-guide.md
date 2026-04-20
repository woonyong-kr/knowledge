---
title: Malloc Lab 작업 가이드 — 구현 대상·규칙·테스트 흐름
category: Malloc lab
keyword: 동적 메모리 할당
created: 2026-04-20
updated: 2026-04-20
tags: [malloc-lab, mm-c, mdriver, memlib, implicit-list, explicit-list, segregated-list, realloc]
summary: mm.c 한 파일에 직접 malloc 을 구현하고 mdriver 로 정확성·성능을 검증하는 Malloc Lab 의 전 과정을 실전 중심으로 정리합니다. 구현 규칙·추천 순서·테스트 옵션·자주 헷갈리는 질문까지 포함합니다.
source: _krafton/SW_AI-W07-malloc-lab/malloc-lab/README.md
---

# Malloc Lab 작업 가이드 — 구현 대상·규칙·테스트 흐름

Malloc Lab 은 `mm.c` 하나에 자신만의 할당기를 구현하고 `mdriver` 로 정확성과 성능을 검증하는 과제입니다. 시작 코드의 `mm.c` 는 동작만 겨우 하는 naive 구현이어서 메모리 재사용도 coalescing 도 없습니다. 이 상태에서 점수 있는 구현으로 끌어올리는 것이 전체 목표입니다.

## 구현 대상

네 개 함수를 직접 구현합니다.

- `mm_init` — 할당기 초기 상태를 세팅합니다. 초기 힙 확장과 첫 free 블록 구성을 여기서 합니다.
- `mm_malloc` — 요청 크기에 맞는 블록을 반환합니다. find_fit → place(split) 의 흐름입니다.
- `mm_free` — 블록을 해제하고 인접 가용 블록과 coalesce 합니다.
- `mm_realloc` — 기존 블록 크기를 변경합니다. in-place 확장·축소를 고려하면 성능이 크게 좋아집니다.

구현 파일은 `mm.c` 하나입니다. 기본 과제에서는 이 파일만 제출합니다.

## 어디부터 읽어야 하는가

코드베이스 진입 순서는 다음이 안정적입니다.

- `mm.c` — 지금 들어 있는 시작 코드를 먼저 봅니다. 팀 정보도 이 파일 상단에서 채웁니다.
- `mm.h` — 구현해야 할 함수 시그니처를 확인합니다.
- `mdriver.c` — 드라이버의 정확성 검사 기준을 봅니다. payload 정렬·힙 범위·블록 겹침 체크가 핵심입니다.
- `config.h` — 어떤 trace 로 테스트하는지, 성능 가중치가 어떻게 되는지 확인합니다.
- `traces/README` — trace 파일 형식과 각 trace 의 의도를 읽어 둡니다.

수정하는 파일은 사실상 `mm.c` 하나입니다. `mdriver.c`, `config.h`, `memlib.{c,h}`, `fsecs.{c,h}`, `fcyc.{c,h}`, `clock.{c,h}`, `ftimer.{c,h}` 는 읽기 전용으로 두는 편이 안전합니다.

## 구현 규칙 네 가지

### (1) 힙은 `mem_sbrk()` 로만 늘립니다

이 과제의 힙은 실제 시스템 힙이 아니라 `memlib` 이 흉내 낸 가상 힙입니다. 새 공간이 필요하면 `mem_sbrk()` 를 호출해 늘립니다. 실제 `sbrk` 나 `mmap` 을 직접 쓰면 측정 기준이 어긋납니다.

### (2) free list 포인터는 빈 블록 내부에 저장합니다

CS:APP 에서 말하는 explicit free list, segregated free list 는 free block 의 페이로드 영역 일부를 prev·next 포인터 저장용으로 씁니다.

```c
[ header | prev ptr | next ptr | ... free payload ... | footer ]
```

할당된 블록에서는 이 prev·next 자리가 그대로 payload 가 됩니다. 할당 상태에 따라 같은 바이트가 다른 의미로 쓰이는 구조입니다.

### (3) free block 관리 노드를 시스템 `malloc()` 으로 따로 받지 않습니다

자신이 구현하는 대상이 이미 `malloc` 입니다. 블록 메타데이터를 시스템 `malloc` 에 숨기면 측정 대상 힙 바깥에 관리 정보를 감추는 셈이 되어 드라이버의 공간 활용도 계산이 왜곡됩니다. 과제 취지에서 이 방식은 반칙에 가깝습니다.

### (4) 전역·정적 포인터는 써도 됩니다

다음 정도는 일반적으로 허용됩니다.

- free list head 를 가리키는 전역 포인터 `static void *free_listp;`
- segregated list 의 head 배열 `static void *seg_heads[LIST_COUNT];`
- rover 포인터(next-fit 용)
- tree root 포인터

핵심 원칙은 "블록마다 개별 노드를 시스템 malloc 으로 받지 않는 것" 입니다. 메타데이터 자체를 힙 바깥으로 빼지 않으면 됩니다.

## 추천 구현 순서

처음부터 복잡한 구조로 가지 말고 단계적으로 가는 편이 안정적입니다.

1. 블록 레이아웃을 먼저 확정합니다. header/footer 형식·할당 비트·크기 단위·정렬 단위를 정합니다.
2. implicit free list 로 끝까지 동작하게 만듭니다. `mm_init`, `extend_heap`, `find_fit`, `place`, `coalesce` 다섯 함수가 작동해야 합니다.
3. `short1-bal.rep`, `short2-bal.rep` 를 통과시킵니다. 아주 작은 trace 이지만 이걸 통과하지 못하면 이후 단계가 모두 꼬입니다.
4. explicit free list 또는 segregated free list 로 확장해 성능을 끌어올립니다.
5. 마지막에 `realloc` 최적화를 얹습니다. 단순히 새 블록을 잡고 복사하는 naive `realloc` 은 trace 점수에 크게 불리합니다.

## 테스트 흐름

프로젝트 디렉터리에서 빌드와 실행이 모두 이루어집니다.

```bash
cd <malloc-lab 디렉터리>
make
```

가장 작은 trace 부터 본 뒤 전체로 확장합니다.

```bash
./mdriver -V -f short1-bal.rep
./mdriver -V -f short2-bal.rep
./mdriver -v   # 전체 기본 trace
./mdriver -h   # 드라이버 옵션 보기
```

자주 쓰는 옵션은 다음입니다.

- `-f <file>` — 특정 trace 만 실행
- `-v` — trace 별 결과 요약
- `-V` — 더 자세한 디버그 출력
- `-l` — libc malloc 과 비교 실행
- `-a` — 팀 정보 체크 생략

## 채점 기준

점수는 크게 두 축입니다. 정확성이 실패하면 성능은 측정되지 않습니다.

정확성 검사는 대략 다음을 봅니다.

- 반환 포인터가 정렬되어 있는가
- payload 가 힙 범위 안에 있는가
- 다른 할당 블록과 겹치지 않는가
- `realloc` 이 기존 데이터를 보존하는가

성능 가중치는 `config.h` 기준으로 활용도(utilization) 60%, 처리량(throughput) 40% 입니다(`UTIL_WEIGHT = 0.60`). 처리량은 libc 기준보다 빠르다고 해서 무한히 이득을 주지 않고 상한이 걸려 있으므로 활용도를 먼저 확보하는 편이 전략적입니다.

## 기본 trace 구성

`config.h` 기본 trace 는 다음 계열로 구성됩니다.

- `short1`, `short2` — 아주 작은 디버깅용
- `amptjp`, `cccp`, `cp-decl`, `expr` — 실제 프로그램 기반 trace
- `binary`, `binary2` — 서로 다른 크기 패턴 대응
- `coalescing` — 병합이 제대로 되는지
- `random`, `random2` — 전반적인 안정성
- `realloc`, `realloc2` — `realloc` 품질 확인

`realloc` trace 가 기본 목록에 포함되어 있으므로 naive `realloc` 은 바로 점수에 반영됩니다. in-place 확장이 가능할 때는 복사 없이 그 자리에서 처리하는 경로를 우선해야 합니다.

## trace 파일 형식

trace 는 다음 형식의 텍스트입니다.

```text
<sugg_heapsize>
<num_ids>
<num_ops>
<weight>
a <id> <bytes>
r <id> <bytes>
f <id>
```

연산 기호 의미는 다음과 같습니다.

- `a` — allocate
- `r` — realloc
- `f` — free

간단 예시.

```text
a 0 512
a 1 128
r 0 640
f 1
f 0
```

## 디버깅 팁

공통으로 쓰이는 방법을 정리합니다.

- 작은 trace 하나를 통과하기 전에는 전체 trace 를 돌리지 않습니다.
- `short1-bal.rep` 이 통과할 때까지 구조 변경을 아끼고 로그와 어설션에 집중합니다.
- block header/footer 출력용 헬퍼 함수를 잠깐 만들어 두면 분기 판단이 쉬워집니다.
- `coalescing-bal.rep` 에서 병합이 안 되면 explicit list 로 올라가도 계속 꼬입니다. 반드시 implicit 단계에서 고치고 넘어갑니다.
- `realloc-bal.rep` 이 느리면 in-place 확장 가능성을 먼저 점검합니다.

## 자주 헷갈리는 질문

### free list 포인터를 구조체로 따로 `malloc` 해서 관리해도 되는가

권장하지 않습니다. 블록 내부에 prev·next 를 저장하는 방식을 써야 하고, list head·tree root·segregated head 배열 같은 전역 포인터만 허용됩니다. per-block 메타데이터를 시스템 malloc 으로 빼는 방식은 과제 취지와 공간 측정 기준에 맞지 않습니다.

### header 와 footer 를 둘 다 두어야 하는가

반드시는 아니지만 초기 구현에서는 footer 까지 두는 편이 coalescing 을 훨씬 단순하게 만듭니다. 성능을 끌어올리는 단계에서 할당 블록의 footer 를 제거하는 최적화(prev-alloc 비트로 대체) 를 도입하는 순서가 안전합니다.

### 처음부터 explicit free list 로 가야 하는가

아닙니다. implicit 으로 정확성을 먼저 맞춘 뒤 explicit 또는 segregated 로 확장하는 순서가 훨씬 안정적입니다. 구조를 한 번에 바꾸면 정확성 문제와 성능 문제가 섞여 원인 추적이 어려워집니다.

## 한 줄 요약

이 과제의 실전 공식은 단순합니다. 팀 정보를 넣고, implicit free list 로 정확성을 먼저 맞추고, explicit 또는 segregated 로 성능을 올리고, 마지막에 `realloc` 을 최적화합니다. 이 순서가 가장 안전하고 실제로도 점수가 가장 많이 오르는 경로입니다.
