---
title: 데이터 검색 과정 — 힙·내부 노드·리프를 거치는 흐름
category: DB
keyword: SQL 엔진
created: 2026-04-20
updated: 2026-04-20
tags: [DB, SQL엔진, INDEX_LOOKUP, TABLE_SCAN, INSERT, DELETE]
summary: minidb 가 INDEX_LOOKUP·TABLE_SCAN·INDEX_DELETE·INSERT 를 수행할 때 페이지를 어떻게 이동하며 행을 찾거나 쓰는지 단계별로 추적합니다.
source: _krafton/SW_AI-W07-SQL/docs/02-데이터-검색-과정.md
---

## 전제 조건

아래 예시는 다음 상태를 가정합니다.

```
테이블: users (id BIGINT, name VARCHAR(32), age INT)
row_size: 44 바이트
행 수: 1000 건
B+ tree 높이: 2 (루트 내부 노드 1 개 + 리프 4 개)
```

```
DB 파일 페이지 배치:
  page 0:  DB 헤더 (root_index_page_id=5, first_heap_page_id=1)
  page 1:  힙 (slot 0~77, id 1~78)
  page 2:  리프 (key 1~291)
  page 3:  힙 (slot 0~77, id 79~156)
  page 4:  리프 (key 292~583)
  page 5:  내부 노드 (루트)
  page 6:  리프 (key 584~875)
  page 7:  힙 (slot 0~77, id 157~234)
  page 8:  리프 (key 876~1000)
  ...
```

## 경로 1 — INDEX_LOOKUP: `SELECT * FROM users WHERE id = 500`

B+ tree 인덱스를 사용하는 O(log n) 검색입니다. id 컬럼에 대한 조건일 때 사용합니다.

```
1 단계: 헤더에서 루트 위치 확인
  page 0 (DB 헤더):
    root_index_page_id = 5
    → "page 5 에서 검색을 시작하라"

2 단계: 루트(내부 노드) 에서 방향 결정
  page 5 (내부 노드):
    leftmost_child = page 2
    entries:
      [0] key=292, right_child=page 4
      [1] key=584, right_child=page 6
      [2] key=876, right_child=page 8

    검색 key=500:
      292 ≤ 500 < 584 → entry[0].right_child = page 4

3 단계: 리프에서 이진 탐색
  page 4 (리프):
    key_count = 292
    entries (key 순서로 정렬됨):
      [0]   key=292, ref={page3, slot58}
      [1]   key=293, ref={page3, slot59}
      ...
      [208] key=500, ref={page7, slot10}  ← 이진 탐색으로 발견
      ...

    → ref = {page_id=7, slot_id=10}

4 단계: 힙에서 실제 데이터 읽기
  page 7 (힙):
    slot[10]: offset=3612, status=ALIVE
    → page7 + 3612 위치에서 44 바이트 읽기
    → [id=500][name="Eve"][age=28]

  row_deserialize → values = {500, "Eve", 28}
  print: "500 | Eve | 28"

총 페이지 접근: page 5 → page 4 → page 7 = 3 회
시간 복잡도: O(log n) + O(log 291) ≈ 트리 탐색 2 회 + 리프 내 이진 탐색
```

## 경로 2 — TABLE_SCAN: `SELECT * FROM users WHERE name = 'Alice'`

name 컬럼에는 인덱스가 없으므로 힙 전체를 순회하는 O(n) 검색입니다.

```
1 단계: 헤더에서 힙 시작 위치 확인
  page 0 (DB 헤더):
    first_heap_page_id = 1

2 단계: 힙 체인을 따라 모든 페이지 순회
  page 1 (힙):
    slot 0: ALIVE → deserialize → name="Bob"   → 불일치, 다음
    slot 1: ALIVE → deserialize → name="Alice" → 일치! 출력
    slot 2: FREE  → 건너뜀
    slot 3: ALIVE → deserialize → name="Charlie" → 불일치
    ...slot 77 까지 검사
    next_heap_page_id = 3

  page 3 (힙):
    slot 0~77 전부 검사
    next_heap_page_id = 7

  page 7 (힙):
    slot 0~77 전부 검사
    next_heap_page_id = 0 (끝)

  → 모든 힙 페이지의 모든 슬롯을 검사

총 페이지 접근: 힙 페이지 전부 (1000 행 / 78 ≈ 13 페이지)
시간 복잡도: O(n) — 1000 건 전부 역직렬화 + 문자열 비교
```

## 경로 3 — INDEX_DELETE: `DELETE FROM users WHERE id = 500`

```
1 단계: B+ tree 에서 id=500 검색 (INDEX_LOOKUP 과 동일)
  page 5 (루트) → page 4 (리프) → ref = {page7, slot10}

2 단계: 힙에서 톰스톤 삭제
  page 7, slot[10]:
    status: ALIVE → FREE
    next_free = 기존 free_slot_head
    free_slot_head = 10

  → 행 데이터(44 바이트) 는 그대로, slot 상태만 변경

3 단계: B+ tree 에서 엔트리 제거
  page 4 (리프):
    entries 배열에서 key=500 제거
    뒤쪽 엔트리를 앞으로 당김 (memcpy)
    key_count-- (292 → 291)

4 단계: 헤더 갱신
  row_count: 1000 → 999
  header_dirty = true
```

## 경로 4 — INSERT: `INSERT INTO users VALUES ('Frank', 35)`

```
1 단계: ID 할당과 직렬화
  id = next_id = 1001
  row_serialize → 44 바이트: [id=1001]["Frank"][age=35]

2 단계: 힙에 행 저장
  find_heap_page():
    page 1 → slot 2 가 FREE → 재활용
    ref = {page_id=1, slot_id=2}

  slot 2: offset=3964 위치에 44 바이트 덮어씀
  slot 2.status = ALIVE

3 단계: B+ tree 에 인덱스 등록
  bptree_insert(key=1001, ref={page1, slot2})

  find_leaf(1001) → page 8 (key 876~1000 이 있던 리프)
  key=1001 은 정렬 위치에 삽입:
    [..., key=999, key=1000, key=1001]

  만약 page 8 이 꽉 차면 분할이 발생합니다.

4 단계: 헤더 갱신
  next_id: 1001 → 1002
  row_count: 999 → 1000
  header_dirty = true
```

## 성능 비교 요약

```
작업                  접근 경로          페이지 읽기 수    시간 복잡도
─────────────────────────────────────────────────────────────────
WHERE id = N          INDEX_LOOKUP       트리높이 + 1     O(log n)
WHERE name = 'X'      TABLE_SCAN         전체 힙 페이지    O(n)
DELETE WHERE id = N   INDEX_DELETE        트리높이 + 1     O(log n)
DELETE WHERE name='X' TABLE_SCAN+DELETE   전체 + α         O(n)
INSERT                INSERT             트리높이 + 1     O(log n)

n = 1,000,000 건 기준:
  INDEX_LOOKUP: ~4 페이지 = 16 KB 읽기
  TABLE_SCAN:   ~12,821 페이지 = 50 MB 읽기
  → 인덱스가 있으면 약 3,000 배 빠름
```

네 가지 경로 모두 "헤더 페이지 → 루트 혹은 힙 시작 → 리프 혹은 힙 체인 → 실제 행" 이라는 동일한 레이어를 따라 내려갑니다. 각 레이어가 한 번의 페이지 I/O 이고, 그 I/O 횟수가 쿼리 성능의 전부입니다.
