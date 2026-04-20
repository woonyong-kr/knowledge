---
title: 슬롯 페이지 레이아웃 가이드 — 헤더·힙·루트 리프
category: DB
keyword: 페이지 스토리지
subkeyword: 슬롯 페이지 레이아웃
created: 2026-04-20
updated: 2026-04-20
tags: [DB, 슬롯페이지, 힙페이지, 헤더페이지, 루트리프]
summary: minidb 가 새 DB 를 만들 때 초기화하는 3 개 페이지(DB 헤더, 첫 힙, 루트 리프) 의 슬롯 기반 레이아웃과 역할을 정리합니다.
source: _krafton/SW_AI-W07-SQL/docs/sql/page-structures-guide.md
---

이 문서는 minidb 데이터베이스 파일에서 처음 만들어지는 3 개의 핵심 페이지를 정리한 가이드입니다.

- 0 번 페이지: DB 헤더 페이지
- 1 번 페이지: 첫 힙 페이지
- 2 번 페이지: 루트 리프 페이지

관련 코드는 다음 파일에 있습니다.

- `src/storage/pager.c`
- `src/storage/table.c`
- `src/storage/bptree.c`
- `include/storage/page_format.h`

## 전체 그림

새 데이터베이스를 만들면 `pager_open(..., create=true)` 가 아래 3 개 페이지를 바로 초기화합니다.

```text
page 0 : DB 전체 메타데이터
page 1 : 실제 row(행) 데이터를 담는 첫 heap page
page 2 : id -> row 위치를 찾기 위한 첫 leaf root page
```

각 페이지의 역할은 다음과 같이 구분할 수 있습니다.

- 헤더 페이지: 데이터베이스 전체 설정과 상태
- 힙 페이지: 실제 행 데이터 저장
- 루트 리프 페이지: 행을 빨리 찾기 위한 인덱스 시작점

## 0 번 페이지: DB 헤더 페이지

0 번 페이지에는 `db_header_t` 구조체가 저장됩니다. 이 페이지는 데이터베이스의 "설명서" 역할을 합니다. 이 파일이 어떤 DB 인지, 페이지 크기는 얼마인지, 다음에 어떤 페이지를 써야 하는지, 현재 테이블 구조가 어떤지 같은 전역 정보를 담습니다.

대표적으로 들어가는 정보는 다음과 같습니다.

- `magic` — 이 파일이 우리 DB 파일이 맞는지 확인하는 식별 문자열
- `version` — DB 포맷 버전
- `page_size` — 한 페이지의 바이트 크기
- `root_index_page_id` — B+ 트리 루트 페이지 번호
- `first_heap_page_id` — 첫 번째 힙 페이지 번호
- `next_page_id` — 새 페이지를 할당할 때 사용할 다음 페이지 번호
- `free_page_head` — 재사용 가능한 free page 리스트의 시작 페이지 번호
- `next_id` — 다음 INSERT 때 자동으로 부여할 id 값
- `row_count` — 현재 저장된 row 수
- `column_count` — 테이블 컬럼 수
- `row_size` — row 하나가 직렬화되었을 때 차지하는 총 바이트 수
- `columns[]` — 각 컬럼의 이름, 타입, 크기, offset 같은 메타 정보

### 생성 직후 예시

새 DB 를 처음 만들면 0 번 페이지는 대략 다음 값을 가집니다.

```text
magic = "MINIDB\0"
version = 1
page_size = 4096
first_heap_page_id = 1
root_index_page_id = 2
next_page_id = 3
free_page_head = 0
next_id = 1
row_count = 0
column_count = 0
row_size = 0
columns = 비어 있음
```

이 상태는 "아직 테이블도 없고 데이터도 없지만, 첫 힙 페이지는 1 번이고 첫 인덱스 루트는 2 번이다" 라는 뜻입니다.

## 1 번 페이지: 첫 힙 페이지

1 번 페이지는 heap page 입니다. 힙 페이지에는 실제 테이블 row 데이터가 저장됩니다.

예를 들어 다음 SQL 을 실행한다고 가정합니다.

```sql
CREATE TABLE users (name VARCHAR(32), age INT);
INSERT INTO users VALUES ('kim', 20);
```

실제로 `(id=1, name="kim", age=20)` 같은 row 본문은 힙 페이지에 저장됩니다.

### 힙 페이지 내부 구조

힙 페이지는 다음과 같이 생겼습니다.

```text
[heap page header][slot 배열 ...][빈 공간][row 데이터들 ...]
```

앞쪽과 뒤쪽이 서로 반대 방향으로 자랍니다.

- 앞쪽: 헤더와 슬롯 배열이 앞에서 뒤로 증가
- 뒤쪽: 실제 row 데이터가 뒤에서 앞으로 증가

### 힙 페이지에 저장되는 정보

#### heap_page_header_t

페이지 전체를 관리하는 헤더입니다.

- `page_type` — 이 페이지가 힙 페이지임을 나타냅니다.
- `next_heap_page_id` — 다음 힙 페이지의 page id. 여러 힙 페이지가 연결 리스트를 이룹니다.
- `slot_count` — 이 페이지에 등록된 슬롯 개수 (alive + free 모두 포함).
- `free_slot_head` — 재사용 가능한 free 슬롯의 시작 번호.
- `free_space_offset` — 뒤에서부터 쓰이기 시작한 row 영역의 오프셋.

#### heap_slot_t

한 row 가 페이지 안에서 어디에 있는지 기록하는 슬롯입니다.

- `offset` — row 가 시작되는 위치 (페이지 내 오프셋).
- `status` — `ROW_ALIVE` 이면 살아 있는 row, `ROW_FREE` 이면 빈 슬롯.
- `next_free` — free 슬롯 체인에서 다음 free 슬롯 번호.

### 생성 직후 예시

새 DB 의 1 번 페이지는 다음 상태로 시작합니다.

```text
page_type = HEAP
next_heap_page_id = 0   (아직 다음 페이지 없음)
slot_count = 0
free_slot_head = NONE
free_space_offset = 4096 (페이지 끝에서 아래로 자랍니다)

슬롯: 비어 있음
row 데이터: 비어 있음
```

"아직 row 하나도 없는 빈 힙 페이지" 라는 뜻입니다. 이후 INSERT 가 들어오면 slot 이 앞에서, row 데이터가 뒤에서 동시에 성장합니다.

## 2 번 페이지: 루트 리프 페이지

2 번 페이지는 B+ tree 의 최초 루트이자 동시에 리프입니다. id 를 키로 삼아 행 위치(`page_id`, `slot_id`) 를 가리키는 엔트리가 여기에 쌓이기 시작합니다.

행 수가 리프의 용량을 넘어서면 새 리프가 생기고, 2 번 페이지는 내부 노드로 승격되거나 다른 페이지와 함께 새로운 루트 아래로 내려갑니다. DB 헤더의 `root_index_page_id` 도 그 시점에 갱신됩니다.

### 초기 상태

```text
page_type = LEAF
parent_page_id = 0  (아직 부모 없음)
key_count = 0
next_leaf_page_id = 0
prev_leaf_page_id = 0
entries = 비어 있음
```

한 페이지 안에서 노드가 "루트" 이면서 "리프" 인 상태는 트리의 높이가 1 일 때만 유지됩니다. 첫 분할 시점에 이 이중 역할이 깨집니다.

## 정리

이 세 페이지가 새 DB 파일의 초기 골격입니다. 헤더가 "어디서 시작하는지" 를 알려주고, 힙 페이지가 "행이 어디에 있는지" 를 담고, 루트 리프가 "어떤 키가 어느 행을 가리키는지" 를 담습니다. 이 세 역할이 분리된 덕분에 같은 4 KB 페이지라는 물리적 단위 위에서 서로 다른 논리 구조를 동시에 얹을 수 있습니다.
