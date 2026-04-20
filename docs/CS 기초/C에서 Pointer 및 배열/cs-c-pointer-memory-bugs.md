---
title: C 메모리 버그 총정리 — 다섯 가지 얼굴과 자주 놓치는 실수
category: CS 기초
keyword: C에서 Pointer 및 배열
created: 2026-04-20
updated: 2026-04-20
tags: [memory-bug, buffer-overflow, use-after-free, double-free, memory-leak, dangling-pointer]
summary: 대표 메모리 버그 다섯 가지와 dangling pointer·memory leak의 차이, 그리고 typical한 실수 코드의 버그 두 가지를 함께 짚어 봅니다.
source: _krafton/SW_AI-W07-SQL/docs/questions/q25-memory-bugs.md
---

# C 메모리 버그 총정리 — 다섯 가지 얼굴과 자주 놓치는 실수

C가 위험하다고 불리는 이유는 언어 설계가 메모리 수명과 경계를 프로그래머에게 맡기기 때문입니다. 이 글은 대표 메모리 버그 다섯 가지를 예시와 함께 정리하고, 자주 혼동되는 dangling pointer와 memory leak의 차이, 그리고 흔히 등장하는 오류 코드 한 편을 직접 디버깅해 봅니다.

## 1. Buffer Overflow (버퍼 오버플로우)

```c
char buf[8];
strcpy(buf, "Hello, World!");  // 13B를 8B 버퍼에 복사
```

- buf 뒤에 있는 메모리(다른 변수, 리턴 주소 등)가 덮어씌워집니다.
- 힙이면 다음 블록의 헤더가 파괴되어 allocator가 오동작합니다.
- 스택이면 리턴 주소가 변조되어 공격자가 코드를 실행할 수 있습니다.

## 2. Use-After-Free (해제 후 사용)

```c
char *p = malloc(100);
free(p);
p[0] = 'A';  // 이미 해제된 메모리에 쓰기
```

- free 후 그 블록은 free list에 들어가고 다른 malloc이 재사용할 수 있습니다.
- p로 쓰면 새로 할당된 다른 데이터를 오염시킵니다.
- 읽기도 위험합니다. 쓰레기 값이거나 다른 사용자의 데이터일 수 있습니다.

## 3. Double Free (이중 해제)

```c
char *p = malloc(100);
free(p);
free(p);  // 같은 블록을 두 번 해제
```

- free list에 같은 블록이 두 번 등록됩니다.
- 이후 malloc 두 번이 같은 주소를 반환해 두 포인터가 같은 메모리를 공유하게 됩니다.

## 4. Memory Leak (메모리 누수)

```c
void foo(void) {
    char *p = malloc(100);
    return;  // free 안 하고 함수 종료
}
```

- p는 스택에 있던 지역 변수라 함수 종료 시 사라집니다.
- malloc한 힙 메모리는 여전히 할당 상태이지만 접근할 방법도, 해제할 방법도 없습니다.
- 장시간 실행되는 서버에서 leak이 쌓이면 OOM(Out of Memory)으로 크래시합니다.

## 5. Uninitialized Read (초기화 안 된 메모리 읽기)

```c
int *p = malloc(sizeof(int));
printf("%d\n", *p);  // 초기화 안 하고 읽기
```

- malloc은 메모리를 0으로 초기화하지 않습니다 (calloc은 합니다).
- 이전에 그 주소를 썼던 프로그램의 잔여 데이터가 남아 있습니다.
- 비결정적 동작 — 디버깅 시 재현이 안 될 수 있습니다.
- 보안: 이전 사용자의 비밀번호, 키 등이 노출될 가능성이 있습니다.

## Dangling Pointer vs Memory Leak

두 버그는 "포인터와 메모리의 수명이 불일치할 때 생긴다"는 점에서 닮았지만, 방향이 반대입니다.

### Dangling Pointer (허상 포인터)

포인터는 남아 있는데 가리키는 메모리가 해제된 상태입니다. "열쇠는 있는데 문이 철거된 것"에 해당합니다.

```c
char *p = malloc(100);
free(p);
// p는 여전히 이전 주소를 가리킴 → dangling pointer
// p를 통해 읽기/쓰기하면 use-after-free 버그
```

### Memory Leak (메모리 누수)

메모리는 할당되어 있는데 가리키는 포인터가 없는 상태입니다. "문은 있는데 열쇠를 잃어버린 것"에 해당합니다.

```c
char *p = malloc(100);
p = malloc(200);  // 이전 100B의 주소를 잃어버림
// 첫 번째 100B는 할당 상태이지만 접근 불가 → leak
```

### 핵심 차이

- Dangling Pointer: 포인터 O, 메모리 X → 접근하면 위험
- Memory Leak: 포인터 X, 메모리 O → 해제 불가, 자원 낭비

둘 다 포인터와 메모리의 수명이 불일치할 때 발생합니다. C에서는 프로그래머가 이 수명을 직접 관리해야 하므로 두 버그 모두 자연스럽게 발생하기 쉽습니다.

## 실전 디버깅 — 아래 코드에서 버그 두 가지를 찾으십시오

원본 코드는 다음과 같습니다.

```c
int **A = malloc(n * sizeof(int));
// ... 사용 ...
A[n] = NULL;
```

### 버그 1: sizeof 타입 불일치

A는 `int**` (포인터의 포인터)입니다. A의 각 원소는 `int*` (포인터)입니다.

- `malloc(n * sizeof(int))` → int 크기(4B)로 n개 할당
- 실제 필요한 건 `int*` 크기(8B)로 n개 할당

x86-64에서:

- `sizeof(int)` = 4바이트
- `sizeof(int*)` = 8바이트
- 절반만 할당되므로 뒤쪽 원소에 접근하면 버퍼 오버플로우가 발생합니다.

수정: `malloc(n * sizeof(int*))`

### 버그 2: 배열 범위 초과 (off-by-one)

```c
A[n] = NULL;
```

A는 n개 원소를 할당했으므로 인덱스는 0 ~ n-1까지 유효합니다. `A[n]`은 할당 범위 바로 다음 메모리에 쓰기이므로 버퍼 오버플로우입니다.

- 다음 블록의 헤더를 NULL(0)로 덮어쓸 수 있습니다.
- allocator 메타데이터가 파괴되어 이후 malloc/free가 비정상 동작합니다.

수정: `A[n-1] = NULL;`

### 수정된 코드

```c
int **A = malloc(n * sizeof(int*));  // int → int*
// ... 사용 ...
A[n-1] = NULL;                       // A[n] → A[n-1]
```
