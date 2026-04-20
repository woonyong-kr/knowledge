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
- 트리의 최대 깊이는 **L10** 으로 제한한다. 그 이하는 자유롭게 중첩해도 된다.
- 기본값은 여전히 L0/L1 폴더다. 포스트 누적이나 단일 원본 분할 필요성이 생기면 해당 가지만 더 깊이 파고 내려간다.
- 하위 키워드를 폴더로 승격하려면 `tree.yaml` 의 `sub` 항목을 문자열에서 객체(`{name, description, slug?, sub?}`) 로 바꾼다 (2.2 절 스키마 참고). 객체는 자기 자신의 `sub` 를 다시 가질 수 있으며, 이것이 깊이 증가의 유일한 수단이다.
- 폴더로 승격된 모든 계층(L2 이하)은 L1 과 동일한 규약(README 마커, 포스트 네이밍, 프런트매터) 을 적용한다.
- 승격 기준은 다음 중 하나를 충족할 때다.
  1. 해당 하위 키워드 하나에 대해 포스트가 2편 이상 누적될 것이 명확한 경우.
  2. 상위 폴더로 들어온 단일 원본이 여러 하위 주제를 커버해 분할이 필요한 경우.
- L11 이상으로는 내려가지 않는다. 그 깊이가 필요하면 상위를 재설계한다.

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
        sub:                     # 선택, 하위 키워드 (문자열과 객체 혼용 가능, 재귀 허용)
          # (a) 문자열: 텍스트로만 표기되는 하위 키워드 (폴더 없음)
          - <하위 키워드명>
          # (b) 객체: 폴더로 승격된 하위 키워드. L1 과 동일한 규약을 그대로 적용.
          - name: <하위 키워드명>
            slug: <override>     # 선택
            description: <개요>
            sub:                 # 선택. 객체는 자기 자신의 sub 를 다시 가질 수 있음 (L10 까지)
              - <더 깊은 하위 키워드명>
              - name: <...>
                description: <...>
                sub: [ ... ]
```

### 2.3 제약
- 키워드명 중복 불가 (동일 L0 내 L1 중복 불가, 전 L1 전역 중복 시 경고).
- `slug` 는 소문자·하이픈만 허용.
- `sub` 는 문자열 또는 객체(`{name, description, slug?, sub?}`) 만 허용한다. 객체는 자기 자신의 `sub` 를 재귀적으로 가질 수 있다.
- 루트(L0) 부터 시작해 최대 깊이는 **L10** 까지만 허용한다. L11 이상은 스키마 자체에서 금지 — 검증 단계에서 실패시킨다.
- 각 계층의 slug 는 상위 slug 와 결합된 포스트 파일명 prefix 를 만들지 않는다. 포스트는 항상 "가장 구체적인 폴더" 의 slug 하나만 사용한다(4.2 절 참고).

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
- 포스트는 해당 키워드의 **L1 폴더** 또는 폴더로 승격된 **L2 폴더** 안에 둔다.
- L0 폴더 직속에는 `README.md` 외 포스트 파일을 두지 않는다. 분류 모호하면 L1 키워드 신설 후 그 안에 둔다.
- 같은 주제를 L1 직속 포스트와 L2 폴더에 동시에 배치하지 않는다. L2 폴더로 승격하면 그 키워드의 포스트는 L2 폴더에만 둔다.

### 4.2 파일명 (슬러그)
형식: `{l0_slug}-{keyword_slug}-{post_slug}.md`
- 모두 소문자, 단어 구분은 하이픈(`-`).
- 한글은 그대로 허용, 공백은 하이픈.
- 예: `cs-부동소수점-floating-point-기초.md`, `os-context-switching-coroutine과의-비교.md`
- `keyword_slug` 는 "해당 포스트가 실제로 놓이는 폴더(가장 구체적인 단계)" 의 slug 를 쓴다. L2 폴더 안 포스트면 L2 slug, 그 외는 L1 slug. `tree.yaml` 에 `slug` 가 있으면 그것을, 없으면 키워드명에서 공백·특수문자 제거 후 소문자화 + 한글 유지로 자동 생성.

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
- 포스트 최상단은 YAML 프런트매터 블록(`---` 로 시작·종료) 으로 연다.
- `created`, `updated` 는 **필수** 필드다. 수기로 `YYYY-MM-DD` 형식 문자열을 적는다. 빌드가 자동 주입하지 않는다.
  - `created`: 해당 포스트를 처음 작성한 날 (작성자가 판단).
  - `updated`: 최근 내용을 실질 수정한 날. 오탈자·마크다운 미세조정 같은 변경은 갱신하지 않아도 된다.
  - 신규 포스트는 `created == updated` 로 시작한다.
- 폴더 깊이에 따라 `keyword` 는 L1 폴더명, `subkeyword` 는 L2 이하 폴더명을 붙인다. L2 보다 깊은 폴더로 승격된 경우에도 `subkeyword` 에 **가장 구체적인 폴더명** 을 적는다(중간 계층은 기록하지 않는다).
- 허용 필드:

```yaml
---
title: 포스트 제목 (한글·영문 자유)
category: CS 기초               # L0 폴더명과 일치
keyword: 실수 표현법            # L1 폴더명과 일치
subkeyword: 부동 소수점          # L2 이하 폴더로 승격된 경우 (가장 구체적인 폴더명)
created: 2026-04-20             # 필수, 수기 입력, YYYY-MM-DD
updated: 2026-04-20             # 필수, 수기 입력, YYYY-MM-DD
tags: [IEEE-754, precision]     # 선택
summary: 1~2문장 요약           # 선택
source: _krafton/.../원본.md    # 원본 기반 재작성인 경우 명시 (선택)
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

## 7. 포스트 작성 스킬 연계

- `docs/` 에 새 포스트를 작성하거나, 기존 포스트를 편집하거나, 외부 원본을 들여와 **복사·이관하는 모든 경우** 에 먼저 `/Users/woonyong/workspace/skills/tech-blog-writing/SKILL.md` 스킬을 읽고 그 규약을 적용한다.
- 적용 범위는 분류와 무관하다. KEEP(원문 유지) 로 판단한 문서조차도 최소한 스킬의 **금지 패턴 체크리스트(이모지·자기계발 어휘·AI 흔적·단정형 과장 등)** 를 통과해야 한다. 통과하지 못하는 구간은 수정 후 반영한다.
- EDIT/REWRITE/SPLIT 로 판단한 문서는 톤(합쇼체·담백한 구어체), 10단계 구조, 제목·부제 규칙, 출력 포맷을 모두 만족시켜야 한다.
- Krafton·외부 원본을 가져오는 경우에도 원본을 그대로 복사하지 않고 스킬의 재작성 흐름에 태운다. 원본의 기술적 사실은 보존하되 문장·구조를 스킬 규약에 맞춘다.
- 직접적인 알고리즘 문제 풀이 문서(`Algorithm 및 Data Structures/*/문제풀이-*.md` 류) 는 복사·이관 대상이 아니다. **알고리즘 개념** 을 설명하는 원본만 스킬에 태워 들여온다 (merge-plan.md 참고).
- 한 원본이 복수 하위 키워드에 걸쳐 있으면 1.2 절의 조건에 따라 폴더로 분할하고, 각 조각을 독립 포스트로 재작성한다.
- 본 스킬과 CONTRIBUTING.md 가 충돌하면 CONTRIBUTING.md (디렉터리·파일명·프런트매터·빌드 규약) 가 우선한다. 스킬은 문장·톤·구조를 다룬다.

---

## 8. 중복 방지 정책

- 동일 키워드가 여러 카테고리에 걸쳐 있으면 **실제 폴더/포스트는 한 곳(캐논)** 에만 둔다.
- 다른 카테고리의 README 에서는 캐논 위치로의 상대 링크만 건다. 폴더를 중복 생성하지 않는다.
- 캐논 위치 이동 시 모든 참조 링크를 함께 갱신.

---

## 9. 키워드 추가·수정·삭제 워크플로

키워드가 매일·매주 추가되어도 트리가 꼬이지 않도록 다음 순서를 반드시 지킨다.

### 9.1 키워드 추가
1. `docs/tree.yaml` 편집 — 새 키워드를 적절한 L0 아래 L1 으로 추가 (필요 시 L2 `sub` 에 항목 추가).
2. `make validate` — 현재 상태 점검 (기존 구조와의 정합성).
3. `make scaffold` — 누락된 폴더·README 자동 생성·관리 구간 갱신.
4. `make validate` — 재실행, 실패 없어야 함.
5. `make build` — `post/` 재생성.
6. 커밋 — 6절 규칙에 따라 단일 커밋 (`commit-convention` 스킬 사용) 후 `git push`.

### 9.2 키워드 이름 변경
1. `docs/tree.yaml` 에서 이름 변경.
2. 해당 폴더를 `git mv` 로 이름 변경 (수동).
3. `make scaffold` → `make validate` → `make build`.
4. 이동된 폴더 하위의 포스트 파일에서 프론트매터 `keyword`, `category` 를 갱신 (필요 시).
5. 커밋 후 `git push`.

### 9.3 키워드 삭제
1. 해당 폴더에 포스트가 남아있는지 확인. 있으면 이동 또는 동반 삭제 여부를 명시적으로 결정.
2. `docs/tree.yaml` 에서 항목 제거.
3. 폴더를 `git rm -r` 로 삭제.
4. `make validate` — 고아 폴더·깨진 링크가 없어야 한다.
5. `make build` — `post/` 미러 반영 (삭제된 포스트가 `post/` 에서도 사라진다).
6. 커밋 후 `git push`.

### 9.4 충돌·꼬임 감지 규칙
`make validate` 는 다음을 차단한다.
- `tree.yaml` 에 정의되었으나 폴더가 없는 경우.
- 폴더가 있으나 `tree.yaml` 에 없는 경우 (고아 폴더).
- README 의 마커 구간 누락 또는 중복.
- 포스트 파일명이 4.2 절 규칙 위배.
- 포스트 프론트매터의 `keyword`·`category` 가 실제 폴더 위치와 불일치.
- L0 슬러그 표에 없는 `l0_slug` 사용.

실패 시 종료 코드 1로 빠져나오므로 커밋 전에 반드시 `make all` 로 한 번 통과시킨다.

---

## 10. 금지 사항 요약

- 폴더·파일명에 숫자 접두사 사용.
- 동일 개념의 폴더를 여러 위치에 중복 생성.
- README 트리 간 키워드 불일치.
- 프론트매터에서 `created`·`updated` 누락, 또는 `YYYY-MM-DD` 외 형식 사용.
- 루트 README 에 트리 외 부가 섹션 추가.
- L0 폴더 직속에 포스트 파일 배치.
- README 의 자동 관리 마커 구간(`<!-- ... -->`) 안쪽을 수동 편집.
- `tree.yaml` 없이 폴더만 수동으로 추가.
- `make build` 없이 커밋·푸시 (빌드 산출물이 최신 상태가 아닐 수 있음).

---

## 11. 대규모 파일 탐색 메타데이터 (`scan-state.yaml`)

### 11.1 위치와 목적
- 파일: `knowledge/scan-state.yaml` (레포 루트).
- 목적: 이 저장소는 포스트·원본·스크립트가 수만 개까지 늘어날 수 있다. 매 지시마다 전수 스캔을 반복하면 컨텍스트가 터진다. scan-state.yaml 은 소스별 마지막 스캔 시점을 기록해, **이후 지시에서는 해당 시점 이후로 수정된 파일만** 살펴보기 위한 메타데이터다.

### 11.2 포맷
```yaml
# scan-state.yaml
version: 1
sources:
  docs:
    last_scanned_at: 2026-04-20T14:30:00+09:00   # 마지막으로 전수 스캔한 시각(로컬 TZ)
    note: docs/ 전체 훑음
  _krafton:
    last_scanned_at: 2026-04-19T22:10:00+09:00
    note: 원본 분류 1차 끝
  uploads:
    last_scanned_at: null
    note: 최근 업로드만 개별 지시로 확인
  _staging:
    last_scanned_at: null
```
- `sources` 하위 키는 상대 경로(디렉터리 또는 파일) 를 사용한다. 존재하지 않는 경로는 에러가 아니라 경고로 처리한다.
- 시각은 ISO 8601 로컬 타임존 포함 포맷이다. 초 단위까지 기록한다.

### 11.3 Claude 동작 규칙
- 파일 탐색·스캔·읽기를 수반하는 지시를 받으면 **가장 먼저** `knowledge/scan-state.yaml` 을 읽는다. (읽지 않으면 규칙 위반으로 간주한다.)
- 스캔 스코프 결정:
  1. `scan-state.yaml` 에 기록이 있고 해당 소스가 존재하면, 이후 조회는 `last_scanned_at` 보다 나중에 변경된 파일만 대상으로 제한한다 (`git log --since`, `find -newermt`, 또는 파일 mtime 비교 등 상황에 맞는 수단을 선택).
  2. `last_scanned_at` 이 `null` 이거나 키가 없으면 전수 스캔으로 간주하고 스캔 완료 후 타임스탬프를 기록한다.
  3. 사용자가 "전수 재스캔" 을 명시하면 기존 타임스탬프를 무시하고 전수 스캔하며 종료 시 타임스탬프만 갱신한다.
- 타임스탬프 갱신 시점은 "Claude 가 실제로 해당 소스를 훑은 직후" 다. 예상만으로 갱신하지 않는다. 타임스탬프 값은 훑기 시작 시각이 아니라 **훑기 완료 시각** 을 기록한다.
- 기록은 즉시 파일에 반영한다. 세션 종료 후에도 후속 세션이 이 값을 신뢰해야 한다.

### 11.4 사용자 동작 규칙
- 저장소에 새 소스(원본 폴더·업로드 등) 가 추가되면 `sources` 에 키를 추가한다. 빌드 스크립트와 무관하므로 수기 편집으로 충분하다.
- 해당 파일은 로컬 관리용이다. 원격 공개 레포에는 커밋하지 않는다 (12 절 참고).

### 11.5 충돌 처리
- 로컬 브랜치 간 병합 시 `scan-state.yaml` 이 충돌하면 **가장 최근 시각** 을 취한다. 시각이 오래된 쪽으로 돌리지 않는다.

---

## 12. 원격 공개 범위 (`.gitignore` 정책)

### 12.1 원칙
- 이 저장소는 **공개 포스트 저장소** 로 운영한다. 원격(GitHub) 에 올라가는 대상은 원칙적으로 `docs/` 디렉터리 안 문서뿐이다.
- 그 외 자산(개인 원본 `_krafton/`, 스테이징 `_staging/`, 빌드 산출물 `post/`, 빌드 스크립트 `scripts/`, 운영 문서 `CLAUDE.md`, `Makefile`, `scan-state.yaml` 등) 은 로컬에만 둔다.

### 12.2 `.gitignore` 규약
- 루트 `.gitignore` 는 "모두 무시 → `docs/` 와 `.gitignore` 자신만 허용" 패턴으로 작성한다.

```gitignore
# 기본값: 전부 무시
/*
# 허용: docs/ 트리와 .gitignore 자신
!/docs/
!/.gitignore
```

- `docs/` 내부에서 추가로 무시하고 싶은 파일이 있으면 `docs/.gitignore` 에 개별 규칙으로 적는다.

### 12.3 이미 추적 중인 파일 해제
- `git rm -r --cached <경로>` 로 원격 추적에서 제외하고, 로컬 파일은 남긴다.
- 대상 예: `scripts/`, `_krafton/`, `_staging/`, `post/`, `Makefile`, `CLAUDE.md`, `scan-state.yaml`, `.DS_Store` 등.
- 해제 후 커밋 메시지는 6 절 커밋 규칙(커밋 컨벤션 스킬) 을 따른다.

### 12.4 검사
- 커밋 직전 `git ls-files` 의 출력이 `docs/` 및 `.gitignore` 경로로만 구성되는지 확인한다.
- `docs/CONTRIBUTING.md` 는 반드시 포함되어야 한다.

### 12.5 한시 문서 처리
- `docs/merge-plan.md` 는 병합 승인 워크플로용 한시 문서다. 병합이 완료되면 삭제한다.
- 삭제 시점: 4 절 파일별 배치표의 KEEP/EDIT/REWRITE/SPLIT/MERGE 대상 이관이 모두 끝나고 `make validate` 가 통과한 직후.
- 삭제 커밋은 6 절 커밋 규칙을 따른다.
