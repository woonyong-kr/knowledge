# DB

<!-- description:start -->
관계형/비관계형 DB, 인덱스, 트리 기반 구조.
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->
- [관계형 DB와 No-SQL DB](./%EA%B4%80%EA%B3%84%ED%98%95%20DB%EC%99%80%20No-SQL%20DB/README.md) — 두 계열의 모델·쿼리·확장성 비교.
- [DB Index](./DB%20Index/README.md) — 인덱스의 목적과 종류·비용.
- [B Tree B+ Tree](./B%20Tree%20B%2B%20Tree/README.md) — 두 트리 구조의 원리와 DB 인덱스에서의 사용.
  - [B+ Tree 노드 구조](./B%20Tree%20B%2B%20Tree/B%2B%20Tree%20%EB%85%B8%EB%93%9C%20%EA%B5%AC%EC%A1%B0/README.md) — 리프·내부 노드 구성과 키·포인터 배치.
  - [리프 내부 노드 분할](./B%20Tree%20B%2B%20Tree/%EB%A6%AC%ED%94%84%20%EB%82%B4%EB%B6%80%20%EB%85%B8%EB%93%9C%20%EB%B6%84%ED%95%A0/README.md) — 삽입 시 리프·내부 노드 분할 알고리즘.
  - [인덱스 탐색 흐름](./B%20Tree%20B%2B%20Tree/%EC%9D%B8%EB%8D%B1%EC%8A%A4%20%ED%83%90%EC%83%89%20%ED%9D%90%EB%A6%84/README.md) — 루트에서 리프까지의 탐색·범위 질의 절차.
  - 페이지 경계 Split
- [페이지 스토리지](./%ED%8E%98%EC%9D%B4%EC%A7%80%20%EC%8A%A4%ED%86%A0%EB%A6%AC%EC%A7%80/README.md) — 디스크 기반 저장의 페이지 단위 레이아웃·타입 태그·슬롯·내부 단편화·memcpy 직렬화.
  - [슬롯 페이지 레이아웃](./%ED%8E%98%EC%9D%B4%EC%A7%80%20%EC%8A%A4%ED%86%A0%EB%A6%AC%EC%A7%80/%EC%8A%AC%EB%A1%AF%20%ED%8E%98%EC%9D%B4%EC%A7%80%20%EB%A0%88%EC%9D%B4%EC%95%84%EC%9B%83/README.md) — 슬롯 디렉터리·tuple 저장 영역으로 나뉜 페이지 내부 구조.
  - [헤더 힙 루트 리프 페이지](./%ED%8E%98%EC%9D%B4%EC%A7%80%20%EC%8A%A4%ED%86%A0%EB%A6%AC%EC%A7%80/%ED%97%A4%EB%8D%94%20%ED%9E%99%20%EB%A3%A8%ED%8A%B8%20%EB%A6%AC%ED%94%84%20%ED%8E%98%EC%9D%B4%EC%A7%80/README.md) — 페이지 타입별 헤더 포맷과 고정 필드·가변 필드 구분.
  - [memcpy 기반 직렬화](./%ED%8E%98%EC%9D%B4%EC%A7%80%20%EC%8A%A4%ED%86%A0%EB%A6%AC%EC%A7%80/memcpy%20%EA%B8%B0%EB%B0%98%20%EC%A7%81%EB%A0%AC%ED%99%94/README.md) — 구조체 memcpy 로 대체하는 가벼운 직렬화·역직렬화 전략.
  - 4KB 페이지 결정 근거
  - 페이지 타입 태그 polymorphism
  - 내부 단편화 측정
- [SQL 엔진](./SQL%20%EC%97%94%EC%A7%84/README.md) — 디스크 기반 미니 SQL 엔진의 전체 구조·프레임 캐시·B+Tree SQL 계획·파서.
  - [SQL 파서](./SQL%20%EC%97%94%EC%A7%84/SQL%20%ED%8C%8C%EC%84%9C/README.md) — SQL 문장을 AST 로 변환하는 파서 구현.
  - [쿼리 플랜](./SQL%20%EC%97%94%EC%A7%84/%EC%BF%BC%EB%A6%AC%20%ED%94%8C%EB%9E%9C/README.md) — AST 에서 실행 계획·연산자 트리를 도출하는 플래너.
  - [프레임 캐시 LRU](./SQL%20%EC%97%94%EC%A7%84/%ED%94%84%EB%A0%88%EC%9E%84%20%EC%BA%90%EC%8B%9C%20LRU/README.md) — 디스크 페이지를 메모리로 올리고 LRU·pin count·dirty bit 로 관리.
  - [pread pwrite](./SQL%20%EC%97%94%EC%A7%84/pread%20pwrite/README.md) — pread·pwrite·O_DIRECT 기반 페이지 입출력과 OS 캐시 상호작용.
  - B+Tree SQL 계획
  - 이중 캐시 의심
  - 성능 테스트 INDEX vs SCAN
- [Redis](./Redis/README.md) — 인메모리 KV 스토어 Redis 의 프로토콜·명령 디스패처·자료구조·TTL·영속성·eviction.
  - [RESP 프로토콜](./Redis/RESP%20%ED%94%84%EB%A1%9C%ED%86%A0%EC%BD%9C/README.md) — Redis 바이너리 안전 텍스트 프로토콜 RESP 의 구조.
  - [명령 디스패처](./Redis/%EB%AA%85%EB%A0%B9%20%EB%94%94%EC%8A%A4%ED%8C%A8%EC%B2%98/README.md) — dict 기반 명령 라우팅과 핸들러 함수 체인.
  - [자료구조](./Redis/%EC%9E%90%EB%A3%8C%EA%B5%AC%EC%A1%B0/README.md) — String·Hash·List·Set·Sorted Set 과 내부 자료구조(Skip List·Hash Table 등).
  - [AOF RDB 영속성](./Redis/AOF%20RDB%20%EC%98%81%EC%86%8D%EC%84%B1/README.md) — AOF append 로그와 RDB 스냅샷의 영속화 전략.
  - MurmurHash3
  - Chained Hash Table
  - Open Address Hash Table
  - TTL lazy active
  - maxmemory eviction
  - 느린 클라이언트 보호
<!-- tree:end -->
