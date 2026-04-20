---
title: React-like 런타임 시스템 아키텍처
category: 프로젝트 공통 지식
keyword: React
created: 2026-04-20
updated: 2026-04-20
tags: [architecture, function-component, hook-runtime, reconciler, renderer, app-integration]
summary: 루트 상태 소유권·자식 stateless 모델을 중심에 둔 React-like 런타임의 계층 설계와 데이터 흐름을 정리합니다.
source: _krafton/SW_AI-W05-react/docs/architecture.md
---

# React-like 런타임 시스템 아키텍처

## 설계 원칙

이 아키텍처는 Hook·VDOM·Diff·Patch 를 설명 가능한 구조로 분리하면서도, 기존 저장소의 VNode·Reconciler·Renderer 자산을 최대한 재사용하도록 구성되어 있습니다. 핵심 원칙은 다음과 같습니다.

- 루트에만 상태를 둡니다.
- 자식은 stateless component 로 유지합니다.
- Hook 상태는 루트 `FunctionComponent` 가 소유합니다.
- VDOM 생성과 DOM 반영을 분리합니다.
- Diff/Patch 계층은 `src/core` 의 기존 모듈을 우선 재사용합니다.

## 상위 구조

이 런타임은 다음 8 개 계층으로 나뉩니다.

1. App Layer
2. Component Runtime Layer
3. Hook Runtime Layer
4. VNode Layer
5. Component Resolver Layer
6. Reconciler Layer
7. DOM Renderer Layer
8. Test Layer

## 계층별 책임

### App Layer

- 루트 컴포넌트 정의, 루트 상태 설계
- 상태 기반 페이지 전환 설계
- 자식 stateless component 구성과 이벤트 연결
- 화면 주제·사용자 흐름 설계

상태 저장의 실제 구현은 직접 갖지 않습니다. 상태 저장과 렌더 예약은 `FunctionComponent` 와 Hook Runtime 이 담당합니다. 여러 페이지는 별도 mount 단위가 아니라 같은 루트 앱 안에서 `currentPage` 같은 상태로 전환됩니다.

### Component Runtime Layer

중심은 `FunctionComponent` 클래스입니다. 최소한 다음 상태를 가집니다.

- `renderFn`
- `hooks`, `hookCursor`
- `currentProps`, `currentVNode`
- `rootElement`, `isMounted`
- `pendingEffects`, `cleanupEffects`

책임은 mount·update·unmount, Hook 실행 컨텍스트 초기화, 렌더 함수 실행, VDOM 교체 시점 제어, effect commit 예약·실행입니다.

자식 컴포넌트는 별도 `FunctionComponent` 인스턴스를 만들지 않습니다. 루트 렌더 중 호출되는 순수 함수이며, `props` 입력에 대해 VNode 를 반환합니다. 이 호출과 전개는 별도의 resolver 계층이 담당합니다.

### Hook Runtime Layer

루트 컴포넌트의 `hooks` 배열을 기반으로 동작합니다. 필수 구성 요소는 다음과 같습니다.

- 현재 활성 루트 컴포넌트를 가리키는 dispatcher
- Hook 인덱스를 증가시키는 cursor
- 상태·effect·memo 슬롯
- dependency 비교 유틸리티
- update scheduling 과 effect commit 유틸리티

`useState` 는 슬롯에 현재 값과 setter 를 저장하고, setter 는 다음 렌더를 예약하거나 즉시 수행합니다. 함수형 업데이트를 허용하고, unmount 이후 setter 는 no-op 입니다.

`useEffect` 는 `deps`, `create`, `cleanup` 슬롯을 가지며 렌더 단계에서는 실행 여부만 결정합니다. 실제 실행은 DOM patch 이후 commit 단계에서 수행하고, 이전 cleanup 이 있으면 새 effect 전에 먼저 호출합니다.

`useMemo` 는 `deps` 와 `value` 를 가지며 dependency 가 유지되면 계산 함수를 재실행하지 않습니다.

### VNode Layer

선언형 UI 를 구조화된 데이터로 바꾸는 계층입니다. 재사용 우선 대상은 `h.js`, `index.js`, `normalizeChildren.js` 입니다. element VNode 생성, 텍스트·배열·중첩 자식 정규화, `key` 와 일반 `props` 분리, 이벤트 prop 전달 구조 유지를 담당합니다.

### Component Resolver Layer

`h(Child, props)` 처럼 선언된 자식 함수형 컴포넌트를 실제 VNode 트리로 전개합니다. 함수형 자식을 식별하고 `props` 를 주입한 뒤 반환값을 일반 VNode 트리로 정규화하며, 자식에서 Hook 사용이 감지되면 명시적 오류를 던집니다. diff 이전 단계에서 최종 렌더 트리를 확정합니다.

### Reconciler Layer

이전 VDOM 과 다음 VDOM 을 비교해 patch 목록을 만듭니다. 재사용 우선 대상은 `diff.js`, `diffChildren.js`, `diffProps.js` 입니다. 노드 교체 판단, 텍스트·props·이벤트 변경 감지, child list 추가·삭제·이동 계산, `key` 기반 항목 매칭을 담당합니다.

### DOM Renderer Layer

patch 를 실제 DOM 에 반영합니다. 재사용 우선 대상은 `createDom.js`, `patch.js`, `applyProps.js`, `applyEvents.js` 입니다. 최초 DOM 생성, patch 적용, 속성 반영, 이벤트 바인딩·교체·해제, 텍스트 갱신을 담당하고, text input 의 `value`, checkbox 의 `checked`, textarea·select 의 `value`, `onInput`·`onChange` 를 통한 상태 반영 같은 기본 form semantics 를 지원합니다.

### Test Layer

단위 테스트는 Hook 슬롯, resolver, diff 결과, patch 동작, memo 캐시, form semantics 를 검증합니다. 기능 테스트는 브라우저 부트스트랩, 사용자 이벤트, 루트 상태 전파, unmount 취소 시나리오를 검증합니다.

## 핵심 데이터 흐름

### 최초 mount

1. 루트 `FunctionComponent` 생성
2. `mount(root, props)` 호출
3. Hook dispatcher 를 현재 루트로 설정
4. 루트 `renderFn(props)` 실행
5. Component Resolver 가 자식 stateless component 전개
6. 최종 VDOM 생성 후 DOM 변환
7. DOM 을 root 에 부착
8. commit 단계에서 effect 실행

### 상태 업데이트

1. `setState` 호출
2. Hook 슬롯 값 갱신
3. update 예약 또는 즉시 실행
4. `hookCursor` 초기화
5. 루트 `renderFn` 재실행
6. Component Resolver 가 자식 stateless component 전개
7. 이전 VDOM 과 새 VDOM diff
8. patch 적용
9. 필요한 cleanup 수행
10. 새 effect 실행

### memo 재사용

`useMemo` 는 렌더 중 계산되지만 dependency 가 같으면 이전 슬롯 값을 그대로 사용합니다. VDOM 자체가 아니라 파생 계산값을 저장합니다.

## 상태 소유권 규칙

이 런타임은 실제 React 처럼 각 컴포넌트가 독립 상태를 갖는 구조를 채택하지 않고, 다음 규칙을 강제합니다.

- 모든 상태는 루트에만 존재합니다.
- 자식은 상태를 만들거나 저장하지 않습니다.
- 자식은 `props` 를 받아 VDOM 을 반환하는 pure rendering function 입니다.
- 여러 자식이 공유하는 값은 루트에서 계산해 props 로 전달합니다.

Lifting State Up 패턴을 구현 수준에서 강제하기 위한 규칙입니다.

## unmount 규칙

루트 `FunctionComponent` 는 종료 시 다음 순서를 따릅니다.

1. 등록된 effect cleanup 실행
2. Hook dispatcher 해제
3. 내부 상태를 unmounted 로 전환
4. 필요 시 root DOM 비우기

`unmount` 는 선택 기능이 아니라 effect lifecycle 을 완결하기 위한 계약입니다.

## Hook 사용 규칙

- Hook 은 루트 렌더 함수 본문에서만 호출합니다.
- 조건문·반복문 내부 Hook 호출은 지원하지 않습니다.
- 자식 컴포넌트 내부 Hook 호출은 지원하지 않습니다.
- Hook 수와 호출 순서는 렌더마다 같아야 합니다.

규칙을 어기면 명시적 오류를 던집니다.

## update scheduling

기본 전략은 설명 가능한 단순 업데이트 모델입니다.

- 기본 구현은 즉시 update 를 허용합니다.
- 확장 구현은 microtask 기반 batching 을 둘 수 있습니다.
- 같은 tick 안의 여러 `setState` 는 마지막 예약된 한 번의 update 로 합칠 수 있습니다.

batching 을 구현하더라도 Hook 규칙과 effect 순서를 깨뜨리지 않습니다.

## 기존 코드와의 연결

- `src/core/vnode`: 선언형 VDOM 생성
- `src/core/reconciler`: diff 계산
- `src/core/renderer-dom`: DOM 생성과 patch
- `src/core/engine`: low-level facade 와 inspect/history 자산 재사용 후보

`engine` 은 일반 VDOM 엔진 중심이므로, 이 구현에서는 그 위에 `FunctionComponent` 와 Hook Runtime 을 얹는 방향을 우선합니다. 공개 API 는 `src/index.js` 에서 노출하고, 브라우저 데모는 `src/app/main.js` 를 엔트리포인트로 삼습니다.

## 앱 통합 아키텍처

앱과 라이브러리의 경계는 다음과 같이 고정합니다.

- 라이브러리 공개 경계: `src/index.js`
- 데모 앱 진입점: `src/app/main.js`
- 데모 HTML root id: `app`

`src/app/main.js` 의 책임은 다음과 같습니다.

- 문서 준비 상태 확인
- `#app` root 조회
- root 부재 시 명시적 오류 발생
- `createApp()` 호출
- 반환된 앱 인스턴스의 `mount()` 실행
- 필요 시 종료 시점에 `unmount()` 연결

앱 구조 원칙은 다음과 같습니다.

- HTML 엔트리는 하나만 유지
- 루트 앱은 하나만 mount
- 대시보드·컬렉션·상세·설정은 별도 앱이 아니라 같은 루트 상태가 렌더하는 페이지 컴포넌트
- 페이지 전환은 `currentPage` 상태 변경으로 처리

`createApp()` 의 책임은 공개 API 옵션 정규화, `FunctionComponent` 생성, engine/facade 와 runtime 연결, `mount`·`updateProps`·`unmount`·`getComponent` 노출이며, 선택 보조 기능으로 `inspect` 를 노출할 수 있습니다.

## 예약 작업과 종료 처리

update scheduling 과 unmount 는 함께 정의되어야 합니다.

- `scheduleUpdate` 는 batching 전략에 따라 즉시 또는 microtask 로 flush 를 예약합니다.
- `unmountComponent` 는 예약된 flush 가 있으면 취소 상태로 전환합니다.
- 취소된 flush 는 실행되더라도 DOM patch 를 수행하지 않습니다.
- commit 전 pending effect 는 폐기합니다.
- commit 완료된 effect 에 대해서만 cleanup 을 실행합니다.

## 다음으로 볼 키워드

- 공개 API 계약 세부
- update 흐름과 microtask batching 세부
- 자식 컴포넌트 전개와 diff/patch 데이터 흐름
