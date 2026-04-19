# docs/ 학습 키워드 트리 운영 지침

이 문서는 `docs/` 디렉터리를 학습 키워드 트리 겸 블로그 포스트 레포로 운영하기 위한 규칙을 정의한다.
모든 신규 폴더·README·포스트 생성, 키워드 이동·삭제, 링크 작성, 빌드·커밋은 본 지침을 따른다.

---

## 1. 디렉터리 구조

### 1.1 폴더 = 키워드
- 폴더명은 키워드 원문을 그대로 사용한다.
- `00-`, `01-` 같은 숫자 접두사 금지.
- 한글, 영문 대소문자, 공백을 그대로 허용한다.

### 1.2 깊이 정책
- 현재 단계는 **L0 (최상위 카테고리)** 와 **L1 (직하위 키워드)** 만 폴더로 만든다.
- L2 이하 키워드는 L1 README 의 트리 구간에 **텍스트로만** 표기하고, 폴더로 만들지 않는다.
- L2 자료가 충분히 쌓이면 본 지침 절차(8절)에 따라 폴더로 승격하고 모든 README 트리를 동기화한다.

### 1.3 특수문자 정규화
원본 키워드에 포함된 파일시스템·URL 친화적이지 않은 문자는 다음 규칙으로 정규화한다.

| 원문 | 처리 | 예시 |
|---|---|---|
| `/` | 공백 치환 | `32 Bit / 64 Bit 차이` → `32 Bit 64 Bit 차이` |
| 수식어 `,` | 공백 치환, 한 폴더 유지 | `Python Call by value, Call by reference` → `Python Call by value Call by reference` |
| 부연 `(...)` | 괄호와 내부 제거 | `시간 복잡도(Big-oh Notation)` → `시간 복잡도` |
| 하위 나열 `(...)` | 괄호 제거하고 내부는 L2 자식으로 분리 | `실수 표현법(부동 소수점, 고정 소수점)` → 폴더 `실수 표현법`, L2 `부동 소수점`·`고정 소수점` |
| `:` | 공백 치환 | `Project 0: PintOS` → `Project 0 PintOS` |
| `~=` 등 기타 기호 | 공백 치환 | `Virtual Machine ~= Hypervisor` → `Virtual Machine Hypervisor` |
| 연속 공백 | 단일 공백 축약 | — |

### 1.4 콤마 나열 분리 정책
원본의 콤마 나열은 의미에 따라 다르게 처리한다. 판단 기준은 "이 항목 아래 별도 포스트가 누적될 가치가 있는가?"이다.

| 패턴 | 처리 | 예시 |
|---|---|---|
| 비교·대조 (`vs`, `차이`) | 하나의 키워드 유지 | `CPU vs GPU`, `jpg png gif 차이` |
| 부모-자식 관계 | 부모를 폴더, 자식은 L2 텍스트 | `정렬, QuickSort, MergeSort, HeapSort` → 폴더 `정렬`, L2 `QuickSort`·`MergeSort`·`HeapSort` |
| 동급 독립 개념 나열 | 각각 별도 L1 폴더로 분리 | `Linked List, Array, Stack, Queue` → 4개 폴더 |
| 짝·세트 개념 (`a/b 패턴`) | 하나의 키워드 유지 | `Recursion Iteration`, `DFS BFS` |

---

## 2. 단일 진실 소스 (SSOT): `docs/tree.yaml`

### 2.1 역할
- 모든 키워드·카테고리·설명·L0 슬러그는 `docs/tree.yaml` 에 정의된다.
- 실제 폴더 구조와 각 README 의 트리 구간은 모두 `tree.yaml` 에서 파생된다.
- 키워드 추가·수정·삭제는 반드시 `tree.yaml` 편집으로 시작한다.

### 2.2 스키마
```yaml
categories:
  - name: <L0 키워드명>          # 필수, 폴더명이 된다
    slug: <l0_slug>              # 필수, 포스트 파일명 prefix 용
    description: <L0 개요>       # 필수, 루트 README 및 L0 README 에 사용
    children:                    # 선택, L1 키워드 목록
      - name: <L1 키워드명>      # 필수
        slug: <override>         # 선택, 지정하지 않으면 자동 생성
        description: <L1 개요>   # 필수
        sub:                     # 선택, L2 키워드 (텍스트만)
          - <L2 키워드명>
          - <L2 키워드명>
```

### 2.3 제약
- 키워드명 중복 불가 (동일 L0 내 L1 중복 불가, 전 L1 전역 중복 시 경고).
- `slug` 는 소문자·하이픈만 허용.
- L2 이하는 문자열 배열로만 표현한다 (더 깊은 중첩 금지).

---

## 3. README 작성 규칙

### 3.1 공통: 자동 관리 구간 마커
모든 README 는 스크립트가 갱신하는 구간을 다음 마커로 감싼다. 마커 안쪽은 사람이 **편집하지 않는다**.

- `<!-- description:start -->` ~ `<!-- description:end -->` : `tree.yaml` 의 description 이 삽입됨
- `<!-- tree:start -->` ~ `<!-- tree:end -->` : 키워드 트리가 삽입됨
- `<!-- posts:start -->` ~ `<!-- posts:end -->` : 이 L1 폴더의 포스트 목록 (L1 README 에만 존재)

마커 **바깥**은 자유 편집 구간으로, 스크립트가 건드리지 않는다.

### 3.2 루트 `docs/README.md`
- 키워드 트리 한 블록만 포함. 메타 설명, 번호, 중복 정리표 같은 부가 섹션 금지.
- 트리는 L0 + L1 만 표시 (L2 이하 제외).
- 각 L0, L1 항목은 동일 이름의 폴더 `README.md` 로 링크.

### 3.3 L0 README (`docs/{L0}/README.md`)
- 상단: L0 개요 (description 구간).
- 본문: L1 키워드 트리. 각 L1 항목은 `[키워드](./키워드/README.md) — 한 줄 설명` 형식.
- L2 자식은 각 L1 바로 아래 들여쓴 텍스트로 표시 (링크 없음).

### 3.4 L1 README (`docs/{L0}/{L1}/README.md`)
- 상단: L1 개요 (description 구간).
- 중단: L2 하위 키워드 트리 (있는 경우).
- 하단: **포스트 목록** 섹션. 이 폴더에 누적된 `.md` 포스트들 링크.

---

## 4. 포스트 파일 규칙

### 4.1 위치
- 포스트는 해당 키워드의 **L1 폴더 안**에 둔다.
- L0 폴더 직속에는 `README.md` 외 포스트 파일을 두지 않는다. 분류 모호하면 L1 키워드 신설 후 그 안에 둔다.

### 4.2 파일명 (슬러그)
형식: `{l0_slug}-{keyword_slug}-{post_slug}.md`
- 모두 소문자, 단어 구분은 하이픈(`-`).
- 한글은 그대로 허용, 공백은 하이픈.
- 예: `cs-부동소수점-floating-point-기초.md`, `os-context-switching-coroutine과의-비교.md`
- `keyword_slug` 는 `tree.yaml` 의 `slug` 가 있으면 그것을, 없으면 L1 키워드명에서 공백·특수문자 제거 후 소문자화 + 한글 유지로 자동 생성.

L0 슬러그 표 (확정):

| L0 키워드 | l0_slug |
|---|---|
| CS 기초 | cs |
| Algorithm 및 Data Structures | algo |
| Malloc lab | malloc |
| 네트워크 | net |
| OS | os |
| Pintos | pintos |
| AI | ai |
| DB | db |
| 프로젝트 공통 지식 | proj |

### 4.3 프론트매터
- `created`, `updated` 같은 날짜 필드는 **수기 입력 금지**. git 커밋 이력에서 빌드 시 자동 주입한다.
- 허용 필드:

```yaml
---
title: 포스트 제목 (한글·영문 자유)
keyword: 실수 표현법            # L1 폴더명과 일치
category: CS 기초               # L0 폴더명과 일치
tags: [IEEE-754, precision]     # 선택
summary: 1~2문장 요약           # 선택
---
```

### 4.4 포스트–README 동기화
- 새 포스트 추가·파일명 변경 시 해당 L1 README 의 포스트 목록 섹션에 항목을 추가·갱신 (스크립트가 자동으로 처리).

---

## 5. 빌드 파이프라인

### 5.1 Makefile 타깃
| 타깃 | 설명 |
|---|---|
| `make help` | 사용 가능한 명령 출력 |
| `make scaffold` | `tree.yaml` 기준으로 폴더·README 의 관리 구간 생성·갱신 |
| `make validate` | `tree.yaml` ↔ 실제 구조 일치 검사 (CI 용) |
| `make build` | `post/` 미러 빌드 (기존 전체 삭제 후 재생성) |
| `make clean` | `post/` 삭제 |
| `make rebuild` | `clean` + `build` |
| `make all` | `validate` + `scaffold` + `build` |

### 5.2 `post/` 디렉터리 규약
- 레포 루트의 `post/` 폴더에 **평탄화**되어 출력된다 (하위 폴더 없음).
- 파일명: `YYYY-MM-DD-{원본_파일명}.md`
  - 예: `docs/CS 기초/실수 표현법/cs-부동소수점-문서1.md` → `post/2026-04-19-cs-부동소수점-문서1.md`
- 날짜는 해당 파일의 **git 최초 add 커밋일** (`git log --diff-filter=A --follow --format=%ad --date=short -1 -- <file>`).
- git 이력이 없으면 오늘 날짜 사용, 표준 에러로 경고 출력.
- 동일 날짜·파일명 충돌 시 `-2`, `-3` 접미사 자동 부여.
- `post/` 는 **커밋 대상이다**. 빌드 산출물을 함께 버전 관리하여 배포 단계에서 바로 사용할 수 있도록 한다.
- 원본 삭제 미러: 매 빌드마다 `post/` 디렉터리를 완전 삭제 후 재생성하므로, 원본이 없어진 포스트는 자동으로 `post/` 에서도 사라진다. 이 변경도 같은 커밋에 포함된다.

### 5.3 스크립트 파일 위치
```
scripts/
├── build_posts.py
├── scaffold.py
└── validate.py
```

---

## 6. 커밋 규칙

- 커밋을 요청받으면 Claude 는 **먼저** `/Users/woonyong/workspace/skills/commit-convention/SKILL.md` 스킬을 읽고 해당 컨벤션을 따라 커밋 메시지를 작성한다.
- 커밋 전에 반드시 다음 순서를 실행한다.
  1. `make validate` 실행 — 이상 없어야 커밋 진행.
  2. `make scaffold` 실행 — `tree.yaml` 변경이 있었다면 폴더·README 자동 갱신.
  3. `make build` 실행 — `post/` 디렉터리를 삭제 후 재생성하여 최신 상태로 만든다.
  4. `git status` 확인 — `docs/`, `post/`, 스크립트 변경이 모두 스테이징 대상인지 점검.
- 단일 논리 변경 (예: 키워드 추가 1건 + 관련 폴더·README 생성 + 빌드 반영)은 **단일 커밋**으로 묶는다.
- `tree.yaml` 편집 결과 반영 시: `tree.yaml`, 생성된 폴더·README, 관련 포스트, 재생성된 `post/` 를 모두 같은 커밋에 포함한다.
- 커밋 후에는 원격 브랜치로 `git push` 한다.

### 6.1 AI·Claude 흔적 금지

- 커밋 메시지 본문·트레일러에 AI/Claude 관련 문구를 **절대 남기지 않는다**. 금지 예시:
  - `Co-Authored-By: Claude ...`, `Co-authored-by: Claude ...`
  - `Generated with Claude Code`, `Generated with Claude` 등 AI 서명 문구 (로봇·스파클 등 연상 이모지 포함)
  - `noreply@anthropic.com` 이 포함된 모든 식별자
- Author/Committer 는 반드시 사용자 본인의 이름·이메일만 사용한다. AI 계정·봇 계정을 지정하지 않는다.
- `--trailer`, `Co-Authored-By`, `Signed-off-by` 등으로 AI 공동 저자를 추가하는 옵션을 사용하지 않는다.
- 이미 남은 흔적을 발견하면 다음 순서로 제거 후 원격을 재작성한다.
  1. `git filter-branch --force --msg-filter 'sed -e "/^Co-Authored-By: Claude/Id" -e "/^Co-authored-by: Claude/Id"' <base>..HEAD`
  2. `git push --force-with-lease origin <branch>`
- 푸시 이후에도 GitHub 웹 UI의 커밋 상세 페이지에서 공동 저자 표시가 사라졌는지 육안 확인한다.

### 6.2 이모지 사용 금지

- 커밋 메시지(제목·본문·트레일러) 와 리포지토리 내 모든 문서(`README.md`, `CONTRIBUTING.md`, `tree.yaml`, 포스트 파일 등) 에 **이모지를 쓰지 않는다**.
- 여기서 "이모지" 는 유니코드 Emoji 속성을 가진 모든 문자(예: `U+1F300–U+1FAFF`, `U+2600–U+27BF`, `U+1F000–U+1F2FF` 범위, 변형 선택자 포함) 를 의미한다.
- 일반 구두점·중점(`·`)·화살표(`→`, `←`) 등 Emoji 속성이 없는 기호는 허용한다.
- 커밋 전 검사: `git diff --cached | grep -P "[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}\x{1F000}-\x{1F2FF}]"` 결과가 비어 있어야 한다.
- 이미 섞여 들어간 이모지를 발견하면 해당 문서에서 제거하고 재커밋하거나, 커밋 메시지라면 6.1 절의 재작성 절차에 따라 이력에서 제거한다.

---

## 7. 중복 방지 정책

- 동일 키워드가 여러 카테고리에 걸쳐 있으면 **실제 폴더/포스트는 한 곳(캐논)** 에만 둔다.
- 다른 카테고리의 README 에서는 캐논 위치로의 상대 링크만 건다. 폴더를 중복 생성하지 않는다.
- 캐논 위치 이동 시 모든 참조 링크를 함께 갱신.

---

## 8. 키워드 추가·수정·삭제 워크플로

키워드가 매일·매주 추가되어도 트리가 꼬이지 않도록 다음 순서를 반드시 지킨다.

### 8.1 키워드 추가
1. `docs/tree.yaml` 편집 — 새 키워드를 적절한 L0 아래 L1 으로 추가 (필요 시 L2 `sub` 에 항목 추가).
2. `make validate` — 현재 상태 점검 (기존 구조와의 정합성).
3. `make scaffold` — 누락된 폴더·README 자동 생성·관리 구간 갱신.
4. `make validate` — 재실행, 실패 없어야 함.
5. `make build` — `post/` 재생성.
6. 커밋 — 6절 규칙에 따라 단일 커밋 (`commit-convention` 스킬 사용) 후 `git push`.

### 8.2 키워드 이름 변경
1. `docs/tree.yaml` 에서 이름 변경.
2. 해당 폴더를 `git mv` 로 이름 변경 (수동).
3. `make scaffold` → `make validate` → `make build`.
4. 이동된 폴더 하위의 포스트 파일에서 프론트매터 `keyword`, `category` 를 갱신 (필요 시).
5. 커밋 후 `git push`.

### 8.3 키워드 삭제
1. 해당 폴더에 포스트가 남아있는지 확인. 있으면 이동 또는 동반 삭제 여부를 명시적으로 결정.
2. `docs/tree.yaml` 에서 항목 제거.
3. 폴더를 `git rm -r` 로 삭제.
4. `make validate` — 고아 폴더·깨진 링크가 없어야 한다.
5. `make build` — `post/` 미러 반영 (삭제된 포스트가 `post/` 에서도 사라진다).
6. 커밋 후 `git push`.

### 8.4 충돌·꼬임 감지 규칙
`make validate` 는 다음을 차단한다.
- `tree.yaml` 에 정의되었으나 폴더가 없는 경우.
- 폴더가 있으나 `tree.yaml` 에 없는 경우 (고아 폴더).
- README 의 마커 구간 누락 또는 중복.
- 포스트 파일명이 §4.2 규칙 위배.
- 포스트 프론트매터의 `keyword`·`category` 가 실제 폴더 위치와 불일치.
- L0 슬러그 표에 없는 `l0_slug` 사용.

실패 시 종료 코드 1로 빠져나오므로 커밋 전에 반드시 `make all` 로 한 번 통과시킨다.

---

## 9. 금지 사항 요약

- 폴더·파일명에 숫자 접두사 사용.
- 동일 개념의 폴더를 여러 위치에 중복 생성.
- README 트리 간 키워드 불일치.
- 프론트매터에 수기 작성일·수정일 입력.
- 루트 README 에 트리 외 부가 섹션 추가.
- L0 폴더 직속에 포스트 파일 배치.
- README 의 자동 관리 마커 구간(`<!-- ... -->`) 안쪽을 수동 편집.
- `tree.yaml` 없이 폴더만 수동으로 추가.
- `make build` 없이 커밋·푸시 (빌드 산출물이 최신 상태가 아닐 수 있음).
