---
title: 디스크 기반 SQL 엔진 Week7 Blueprint
category: DB
keyword: SQL 엔진
created: 2026-04-20
updated: 2026-04-20
tags: [DB, SQL엔진, Blueprint, 저장엔진, 로드맵]
summary: 파서·플래너·실행기·페이저·슬롯 힙·B+ tree 로 이어지는 minidb 의 전체 아키텍처와 구현 순서를 7 단계로 정리한 청사진입니다.
source: _krafton/SW_AI-W07-SQL/docs/sql/week7-bptree-sql-blueprint.md
---

## 목표

저장 엔진은 처음부터 새로 만들고, parser 는 기존 구조를 참고해 이번 과제에 필요한 최소 문법으로 간소화합니다. `입력 → 파싱 → 실행 → 저장소` 경계는 명확하게 유지합니다.

기본 목표는 "저장 엔진 심화형" 패키지입니다. 단순한 insert·select 데모가 아니라, `pager + slotted heap + B+ tree + delete/reuse + 방어 코드` 까지 설명 가능한 수준으로 만드는 것이 목표입니다.

## 작업 방식

- 팀 분업이 아니라, 1 인 또는 전원이 같은 프롬프트로 전체를 함께 만듭니다.
- 목표는 "분업으로 빠르게 완성" 이 아니라 "전 과정을 이해하며 구현" 입니다.
- AI 로 코드를 생성하더라도, 생성된 코드의 핵심 로직은 반드시 이해하고 설명할 수 있어야 합니다.
- 각 Step 을 순서대로 밟되, 이전 Step 이 안정화된 뒤 다음으로 넘어갑니다.

## 최종 데모 기준

- `INSERT` 시 id 자동 증가
- row 는 `.db` 파일의 heap page 에 저장
- `id -> row_ref` 는 B+ tree leaf 에 저장
- `SELECT ... WHERE id = ?` 는 인덱스 사용
- `SELECT ... WHERE name = ?` 는 heap scan 사용
- `DELETE` 후 tombstone 과 free slot·page 재사용이 동작
- `EXPLAIN`, `.btree`, `.pages` 로 내부 구조 설명 가능
- 재실행 후에도 데이터와 `next_id` 유지
- 100 만 건 이상 insert 후 `id lookup` 과 `non-id scan` 성능 비교

## 권장 아키텍처

```text
input
  -> lexer/parser
  -> statement AST
  -> planner
  -> executor
  -> storage engine
      -> schema layout
      -> pager (page frame cache)
      -> slotted heap table
      -> b+ tree (on-disk, page 기반)
      -> page allocator (free page list)
      -> database.db
```

핵심 규칙은 여섯 가지입니다.

1. parser 는 storage 를 직접 호출하지 않습니다.
2. planner 가 `WHERE id = ?` 인 경우 `INDEX_LOOKUP` 또는 `INDEX_DELETE` 를 선택합니다.
3. row 는 heap page 에 저장하고, B+ tree leaf 에는 `key + row_ref` 만 저장합니다.
4. row 별 `malloc()` 을 피하고 page 중심 메모리 모델을 유지합니다.
5. delete 는 file compaction 이 아니라 tombstone 과 free list 재사용으로 처리합니다.
6. B+ tree 의 노드는 파일의 page 입니다. 자식을 포인터가 아니라 page 번호로 가리킵니다.

## 이번 과제의 핵심 개념

### DB 의 성능은 파일을 몇 번 읽느냐가 결정한다

100 만 건 기준입니다.

- Table Scan: heap page 약 33,334 개 전부 읽기
- B+ Tree: root → internal → leaf → heap = page 4 개

이 차이가 B+ Tree 를 쓰는 이유의 전부입니다.

### malloc 경험이 직접 적용되는 지점

| malloc 과제 | 이번 DB 과제 | 연결 |
|-------------|-------------|------|
| 힙 영역을 페이지처럼 관리 | DB 파일을 페이지 배열로 관리 | 공간을 미리 잡고 블록 단위로 분배 |
| free list 로 빈 블록 재사용 | free slot·free page list 로 재사용 | tombstone 기반 재활용 |
| coalesce 로 단편화 억제 | 필요 시 page compact | 인접 빈 공간 병합은 생략 |
| split 으로 큰 블록을 분할 | B+ tree split 으로 노드 분할 | 경계 계산이 핵심 |

## 7 단계 구현 순서

Step 1. 파일 열기와 page 0 초기화
Step 2. pager + 프레임 캐시 (LRU, pin, dirty bit)
Step 3. slotted heap page (INSERT/SELECT 스캔)
Step 4. B+ tree leaf 전용(단일 노드) INSERT/SELECT
Step 5. B+ tree split, 내부 노드, 루트 교체
Step 6. DELETE, tombstone, free slot/page 재사용
Step 7. EXPLAIN, `.btree`, `.pages`, 벤치마크

각 Step 이 안정화된 뒤에야 다음 단계로 넘어갑니다. 특히 Step 5 전에 반드시 Step 4 까지가 100% 동작해야 합니다. split 경로는 여러 페이지를 동시에 건드리므로, 단일 노드 경로가 탄탄하지 않으면 디버깅이 몇 배 어려워집니다.

## 이번 주에서 제외한 범위

- 트랜잭션
- crash recovery
- WAL
- UPDATE
- 다중 인덱스
- multi-table 일반화
- 가변 길이 row
- cost-based SQL optimizer 일반화
- page-level latch coupling
- VACUUM 실제 구현

핵심은 다음 한 줄입니다.

> 디스크 저장 + SQL 경계 유지 + id 인덱스 적용 + 삭제와 재사용 경로 설명 가능.

## 정리

이 Blueprint 는 "작은 SQL 엔진을 한 주에 끝까지 만들어 낸다" 는 목표보다 "한 주에 저장 엔진의 바닥까지 한 번은 닿아 본다" 는 목표에 더 가깝습니다. 그래서 기능 폭을 일부러 좁혔고, 대신 페이지·힙·B+ tree·free list·tombstone 의 경로가 끊김 없이 하나의 저장소 위에서 동작하는 것을 확인하는 데 집중했습니다.
