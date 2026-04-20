---
title: C 메모리 기반 추상화 패턴 — 클래스 없이 페이지 타입을 만드는 방법
category: DB
keyword: 페이지 스토리지
subkeyword: 헤더 힙 루트 리프 페이지
created: 2026-04-20
updated: 2026-04-20
tags: [DB, 페이지타입, C, packed, memcpy]
summary: C++ 클래스 기반 직렬화와 C 의 packed 구조체 + memcpy 기반 페이지 추상화를 나란히 놓고, minidb 가 같은 바이트를 여러 구조체로 해석하는 방식을 정리합니다.
source: _krafton/SW_AI-W07-SQL/docs/05-C-메모리-추상화-패턴.md
---

## 1. 핵심 아이디어

C++, Java, Python 에서는 클래스로 데이터와 동작을 묶습니다. C 에는 클래스가 없습니다. 대신 바이트 배열(`uint8_t *`) 과 packed 구조체와 memcpy 조합으로 동일한 추상화를 달성합니다.

minidb 에서 이 패턴이 프로젝트 전체를 관통하는 핵심 설계입니다.

## 2. C++ 클래스 vs C 메모리 캐스팅

### C++ 로 B+ tree 리프를 만든다면

```cpp
class LeafNode {
private:
    uint32_t page_type = PAGE_TYPE_LEAF;
    uint32_t parent_page_id;
    uint32_t key_count;
    uint32_t next_leaf;
    uint32_t prev_leaf;
    vector<LeafEntry> entries;

public:
    void insert(uint64_t key, RowRef ref);
    bool search(uint64_t key, RowRef &out);
    void serialize(uint8_t *buf);       // 메모리 → 디스크 변환
    void deserialize(uint8_t *buf);     // 디스크 → 메모리 변환
};

// 사용:
LeafNode node;
node.deserialize(disk_data);   // 디스크에서 읽어서 객체로 변환
node.insert(key, ref);         // 메서드 호출
node.serialize(disk_data);     // 다시 디스크 형태로 변환
```

문제는 직렬화와 역직렬화 오버헤드가 매번 발생한다는 점입니다.

### C (minidb) 는 이렇게 합니다

```c
// 구조체가 곧 디스크 포맷
typedef struct {
    uint32_t page_type;
    uint32_t parent_page_id;
    uint32_t key_count;
    uint32_t next_leaf_page_id;
    uint32_t prev_leaf_page_id;
} __attribute__((packed)) leaf_page_header_t;

typedef struct {
    uint64_t  key;
    row_ref_t row_ref;
} __attribute__((packed)) leaf_entry_t;
```

디스크에서 읽은 `uint8_t *buf` 가 곧 `leaf_page_header_t *` 입니다. 캐스팅 한 번이면 필드에 바로 접근할 수 있고, 수정 후에는 그 바이트를 그대로 디스크에 씁니다. 직렬화와 역직렬화라는 별도 단계가 사라집니다.

## 3. packed 구조체가 필요한 이유

`__attribute__((packed))` 가 없으면 컴파일러는 성능을 위해 필드 사이에 패딩을 넣습니다. 같은 구조체가 x86_64 와 ARM 에서 서로 다른 크기로 메모리에 배치될 수 있습니다. 이 경우 디스크에 쓴 바이트 레이아웃과 다음 실행에서 읽은 레이아웃이 어긋납니다.

packed 를 붙이면 필드가 선언 순서대로 패딩 없이 연속 배치됩니다. 대신 비정렬 접근이 발생할 수 있어 약간의 성능 저하가 있습니다. minidb 는 필드 순서를 수동으로 맞춰 대부분의 필드가 4 바이트 또는 2 바이트 정렬에 놓이도록 했으므로 실질 성능 손실은 거의 없었습니다.

## 4. 페이지를 "블록의 해석" 으로 본다

같은 4 KB 버퍼를 필요에 따라 서로 다른 구조체 포인터로 캐스팅합니다.

```c
Frame *f = pager_get_page(pager, pn);
PageType t = *(PageType *)f->data;

if (t == PAGE_TYPE_HEAP) {
    HeapPageHeader *h = (HeapPageHeader *)f->data;
    h->slot_count++;
} else if (t == PAGE_TYPE_BPLUS_LEAF) {
    BPlusLeafHeader *l = (BPlusLeafHeader *)f->data;
    l->n_keys++;
}
```

한 버퍼를 A 타입으로도 B 타입으로도 해석할 수 있습니다. 모든 페이지 타입이 첫 4 바이트에 `page_type` 을 공유하고, 그 값 하나로 "지금 어떤 구조체로 보아야 하는가" 를 결정합니다. 클래스가 없어도 타입 구분이 가능합니다.

## 5. 이 추상화가 얻는 것

- 런타임 비용 제로 — 캐스팅은 컴파일 타임에 사라지므로 실행 시 오버헤드가 없습니다.
- 디스크와 메모리의 포맷 동일 — `pread` 로 읽은 바이트를 그대로 구조체로 해석하므로 변환이 필요 없습니다.
- 같은 버퍼를 여러 역할로 재활용 — 프레임 하나가 지금은 힙 페이지였다가 다음 순간 리프 페이지가 될 수 있습니다. 타입 태그만 바뀌면 그만입니다.

## 6. 이 추상화의 대가

- 스키마 진화가 어렵습니다. 필드 하나를 추가하려면 페이지 포맷 자체를 버전 관리해야 합니다.
- 언어 간 공유가 어렵습니다. 다른 언어에서 같은 파일을 읽으려면 구조체 레이아웃을 그대로 흉내 내야 합니다.
- 엔디안과 정렬이 고정됩니다. 크로스 플랫폼으로 쓰려면 big-endian 이나 가변 정수 같은 규약을 따로 선언해야 합니다.

minidb 는 로컬 파일 포맷 한정이므로 이 제약을 전부 받아들였습니다. 그 대가로 직렬화 계층 전체를 제거했고, 페이지 하나를 읽고 쓰는 핫 패스가 `pread` + 캐스팅 두 단계로 끝납니다.

## 7. 정리

C 에는 클래스도 가상 함수도 없지만, packed 구조체와 바이트 캐스팅과 `page_type` 태그로 "블록의 해석" 이라는 다른 종류의 다형성을 구현할 수 있습니다. 메모리 표현과 디스크 표현이 같다는 설계 선택이 이 추상화의 핵심이며, 이 설계가 직렬화 비용을 제거해 DB 엔진의 핫 패스를 단순하게 만듭니다.
