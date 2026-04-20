---
title: C 포인터와 참조형 동작 — 예제로 정리하기
category: CS 기초
keyword: C에서 Pointer 및 배열
created: 2026-04-20
updated: 2026-04-20
tags: [C, pointer, reference, linked-list, double-pointer]
summary: C에는 C++의 reference가 없으므로 "주소를 넘겨 원본을 바꾸는 방식"으로 참조처럼 동작시킵니다. 자료구조 문제에서 자주 막히는 포인터 개념을 예제로 정리합니다.
source: _krafton/SW-AI-W06-data_structures_docker/docs/c-pointer-reference-examples.md
---

# C 포인터와 참조형 동작 — 예제로 정리하기

이 글은 자료구조 과제를 풀면서 가장 많이 막히는 포인터 개념을 실제 예제로 이해하기 위해 정리한 문서입니다.

먼저 한 가지를 분명히 하고 시작합니다.

- C++에는 `reference` 문법이 있습니다.
- C에는 C++의 참조 문법이 없습니다.
- 대신 C에서는 "주소를 넘겨서 바깥 값을 바꾸는 방식"으로 참조처럼 동작시킵니다.

즉 여기서 말하는 `reference`는 대부분 아래 둘 중 하나입니다.

- 어떤 변수의 주소를 가리키는 포인터
- 그 포인터를 함수에 넘겨서 원본을 바꾸는 방식

## 1. 가장 기본: 값과 주소

```c
#include <stdio.h>

int main(void) {
    int x = 10;
    int *p = &x;

    printf("x = %d\n", x);
    printf("&x = %p\n", (void *)&x);
    printf("p = %p\n", (void *)p);
    printf("*p = %d\n", *p);

    *p = 30;
    printf("after *p = 30, x = %d\n", x);
    return 0;
}
```

핵심:

- `x`는 값
- `&x`는 `x`의 주소
- `p`는 주소를 저장한 변수
- `*p`는 그 주소가 가리키는 실제 값

여기서 가장 중요하게 구분할 것:

- `p = &x;` 는 포인터가 가리키는 대상을 정하는 것
- `*p = 30;` 은 원본 값 `x`를 바꾸는 것

## 2. 포인터 변수와 포인터가 가리키는 값은 다릅니다

```c
#include <stdio.h>

int main(void) {
    int a = 3;
    int b = 7;
    int *p = &a;

    printf("*p = %d\n", *p);  // 3

    p = &b;
    printf("*p = %d\n", *p);  // 7

    *p = 100;
    printf("b = %d\n", b);    // 100
    return 0;
}
```

여기서 일어난 일:

- 처음엔 `p`가 `a`를 가리킵니다.
- 나중엔 `p`가 `b`를 가리키도록 바뀝니다.
- 마지막 `*p = 100`은 현재 가리키는 대상인 `b`를 바꿉니다.

즉 `p`를 바꾸는 것과 `*p`를 바꾸는 것은 완전히 다릅니다.

## 3. 함수에 값을 넘기면 원본은 바뀌지 않습니다

```c
#include <stdio.h>

void set_value(int x) {
    x = 99;
}

int main(void) {
    int n = 10;
    set_value(n);
    printf("n = %d\n", n);  // 10
    return 0;
}
```

이유:

- C는 기본적으로 값 전달입니다.
- `set_value(n)`을 호출하면 `n`의 값이 복사되어 `x`로 들어갑니다.
- 함수 안에서 바뀌는 건 복사본 `x`입니다.

## 4. 주소를 넘기면 원본을 바꿀 수 있습니다

```c
#include <stdio.h>

void set_value(int *p) {
    *p = 99;
}

int main(void) {
    int n = 10;
    set_value(&n);
    printf("n = %d\n", n);  // 99
    return 0;
}
```

이것이 C에서 "참조처럼" 동작하는 대표 예시입니다.

- `&n`으로 주소를 넘깁니다.
- 함수는 `int *p`로 받습니다.
- `*p = 99`로 원본 `n`을 바꿉니다.

## 5. swap 예제로 이해하기

잘못된 버전:

```c
void swap_wrong(int a, int b) {
    int temp = a;
    a = b;
    b = temp;
}
```

올바른 버전:

```c
void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}
```

사용:

```c
int x = 3;
int y = 5;
swap(&x, &y);
```

왜 포인터가 필요한가:

- 바깥 변수 두 개를 직접 바꾸려면 두 변수의 주소를 알아야 하기 때문입니다.

## 6. 배열과 포인터

```c
#include <stdio.h>

int main(void) {
    int arr[3] = {10, 20, 30};
    int *p = arr;

    printf("%d\n", arr[0]);   // 10
    printf("%d\n", *p);       // 10
    printf("%d\n", *(p + 1)); // 20
    printf("%d\n", p[2]);     // 30
    return 0;
}
```

핵심:

- 배열 이름 `arr`는 많은 상황에서 첫 원소 주소처럼 동작합니다.
- `arr[i]`와 `*(arr + i)`는 같은 계열입니다.

연결되는 주제:

- 문자열 처리
- 입력 버퍼
- 배열 기반 순회
- 포인터 이동

## 7. 문자열도 결국 `char *`

```c
#include <stdio.h>

int main(void) {
    char str[] = "abc";
    char *p = str;

    printf("%c\n", *p);       // a
    printf("%c\n", *(p + 1)); // b
    return 0;
}
```

주의:

- 문자열은 마지막에 `'\0'`이 있습니다.
- 끝을 넘어서 읽으면 안 됩니다.

## 8. 구조체와 포인터

```c
#include <stdio.h>

typedef struct {
    int value;
} Node;

int main(void) {
    Node node = {42};
    Node *p = &node;

    printf("%d\n", node.value);
    printf("%d\n", (*p).value);
    printf("%d\n", p->value);
    return 0;
}
```

기억할 것:

- `(*p).value`와 `p->value`는 같습니다.
- 자료구조 문제에서는 `->`를 계속 씁니다.

## 9. Linked List에서 포인터가 왜 중요한가

```c
typedef struct _listnode {
    int item;
    struct _listnode *next;
} ListNode;
```

이 한 줄이 핵심입니다.

- `next`는 다음 노드의 주소입니다.
- 연결 리스트를 바꾼다는 건 결국 `next` 값을 바꾼다는 뜻입니다.

예를 들어 맨 앞 삽입:

```c
ListNode *newNode = malloc(sizeof(ListNode));
newNode->item = 100;
newNode->next = head;
head = newNode;
```

여기서 순서가 중요합니다.

1. 새 노드 만들기
2. 새 노드의 `next`를 기존 head로 연결
3. head를 새 노드로 바꾸기

## 10. head를 함수 안에서 바꾸려면 왜 이중 포인터가 필요한가

잘못된 예:

```c
void push_front_wrong(ListNode *head, int value) {
    ListNode *newNode = malloc(sizeof(ListNode));
    newNode->item = value;
    newNode->next = head;
    head = newNode;
}
```

왜 틀렸나:

- 함수 안의 `head`는 복사본입니다.
- 함수 밖 원래 head는 바뀌지 않습니다.

올바른 예:

```c
void push_front(ListNode **ptrHead, int value) {
    ListNode *newNode = malloc(sizeof(ListNode));
    newNode->item = value;
    newNode->next = *ptrHead;
    *ptrHead = newNode;
}
```

사용:

```c
push_front(&head, 10);
```

자주 등장하는 형태:

- `moveMaxToFront(ListNode **ptrHead)`
- `RecursiveReverse(ListNode **ptrHead)`

이런 형태는 head 자체를 바꾸기 때문에 이중 포인터를 쓰는 경우가 많습니다.

## 11. 포인터를 따라가며 순회하기

```c
ListNode *cur = head;
while (cur != NULL) {
    printf("%d\n", cur->item);
    cur = cur->next;
}
```

여기서:

- `cur`는 순회용 포인터
- 원본 `head`는 유지

실전 팁:

- 순회할 때 원본 head를 직접 움직이지 말고 `cur`를 따로 두는 게 안전합니다.

## 12. 삭제할 때 가장 많이 하는 실수

예:

```c
ListNode *temp = cur->next;
cur->next = temp->next;
free(temp);
```

주의:

- 연결을 먼저 바꿀지
- 다음 노드를 미리 저장할지
- free 후 다시 읽지 않을지

잘못된 예:

```c
free(temp);
cur->next = temp->next; // 이미 해제된 메모리 접근
```

## 13. `malloc`과 `free`

기본 예제:

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(sizeof(int));
    if (p == NULL) {
        return 1;
    }

    *p = 123;
    printf("%d\n", *p);
    free(p);
    return 0;
}
```

핵심:

- `malloc`은 heap 메모리를 받습니다.
- 안 쓰면 `free`해야 합니다.
- `free` 후에는 다시 쓰지 않습니다.

## 14. `NULL` 체크

세그폴트 원인 1순위입니다.

```c
if (head == NULL) {
    return;
}
```

혹은:

```c
while (cur != NULL) {
    ...
}
```

안전하게 가려면:

- 빈 리스트
- 노드 1개
- 첫 노드 삭제
- 마지막 노드 삭제

를 항상 따로 생각합니다.

## 15. Queue와 Stack도 포인터 흐름으로 보면 쉽습니다

Queue:

- 뒤에 넣고
- 앞에서 뺀다

Stack:

- 앞에 넣고
- 앞에서 뺀다

즉 구현 차이는 결국 포인터 연결 방향과 삽입 위치 차이입니다.

## 16. 실제로 손으로 테스트해 볼 예제

### 예제 1. head가 바뀌는지 확인

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int value;
    struct Node *next;
} Node;

void push_front(Node **ptrHead, int value) {
    Node *newNode = malloc(sizeof(Node));
    newNode->value = value;
    newNode->next = *ptrHead;
    *ptrHead = newNode;
}

void print_list(Node *head) {
    Node *cur = head;
    while (cur != NULL) {
        printf("%d ", cur->value);
        cur = cur->next;
    }
    printf("\n");
}

void free_list(Node *head) {
    Node *cur = head;
    while (cur != NULL) {
        Node *next = cur->next;
        free(cur);
        cur = next;
    }
}

int main(void) {
    Node *head = NULL;
    push_front(&head, 3);
    push_front(&head, 2);
    push_front(&head, 1);
    print_list(head); // 1 2 3
    free_list(head);
    return 0;
}
```

### 예제 2. swap으로 원본 변경 확인

```c
#include <stdio.h>

void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

int main(void) {
    int x = 10;
    int y = 20;
    swap(&x, &y);
    printf("%d %d\n", x, y); // 20 10
    return 0;
}
```

### 예제 3. 잘못된 포인터 사용이 왜 위험한지 보기

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(sizeof(int));
    *p = 10;
    free(p);

    // 여기서 *p를 읽거나 쓰면 undefined behavior
    // printf("%d\n", *p);
    return 0;
}
```

이 예제는 "운 좋으면 돌아가는 것처럼 보여도 틀린 코드"라는 것을 보여줍니다.

## 17. 자료구조 문제에서 꼭 구분할 것

- `ListNode *head` 와 `ListNode **ptrHead`
- `p`와 `*p`
- 순회용 포인터와 원본 포인터
- 기존 노드를 재배치하는 것과 새 노드를 생성하는 것
- `malloc`으로 받은 메모리와 지역변수 메모리
- 연결 변경과 메모리 해제 순서

## 18. 직접 테스트할 때 추천 질문

- 지금 바꾸는 건 포인터 변수인가, 원본 값인가
- 이 함수가 끝난 뒤에도 이 노드는 살아 있어야 하나
- head가 바뀌는 상황인가
- free 이후 다시 접근하는 코드가 있나
- 빈 리스트/노드 1개일 때도 동작하나

## 19. 직접 컴파일해서 확인하는 방법

예를 들어 `pointer_demo.c`로 저장했다면:

```bash
gcc -Wall -Wextra -g pointer_demo.c -o pointer_demo
./pointer_demo
```

메모리 문제까지 보고 싶다면:

```bash
valgrind --leak-check=full ./pointer_demo
```

## 20. 한 줄 요약

- C에는 C++ reference 문법이 없고, 주소를 넘겨서 참조처럼 동작시킵니다.
- 자료구조 문제는 결국 "포인터 연결을 안전하게 바꾸는 문제"입니다.
- head 변경, `malloc/free`, `NULL` 체크, 이중 포인터를 이해하면 절반 이상은 정리됩니다.
