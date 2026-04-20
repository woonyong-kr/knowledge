# SQL 엔진

<!-- description:start -->
디스크 기반 미니 SQL 엔진의 전체 구조·프레임 캐시·B+Tree SQL 계획·파서.
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->
- [SQL 파서](./SQL%20%ED%8C%8C%EC%84%9C/README.md) — SQL 문장을 AST 로 변환하는 파서 구현.
- [쿼리 플랜](./%EC%BF%BC%EB%A6%AC%20%ED%94%8C%EB%9E%9C/README.md) — AST 에서 실행 계획·연산자 트리를 도출하는 플래너.
- [프레임 캐시 LRU](./%ED%94%84%EB%A0%88%EC%9E%84%20%EC%BA%90%EC%8B%9C%20LRU/README.md) — 디스크 페이지를 메모리로 올리고 LRU·pin count·dirty bit 로 관리.
- [pread pwrite](./pread%20pwrite/README.md) — pread·pwrite·O_DIRECT 기반 페이지 입출력과 OS 캐시 상호작용.
- B+Tree SQL 계획
- 이중 캐시 의심
- 성능 테스트 INDEX vs SCAN
<!-- tree:end -->

## 포스트

<!-- posts:start -->
(없음)
<!-- posts:end -->
