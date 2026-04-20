---
title: React-like 런타임과 Fiber 의 구조 차이
category: 프로젝트 공통 지식
keyword: React
subkeyword: Fiber 아키텍처
created: 2026-04-20
updated: 2026-04-20
tags: [fiber, reconciliation, class-diagram, function-component, scheduler, synthetic-event]
summary: 직접 구현한 React-like 런타임의 클래스 구조를 정리하고 실제 React Fiber 모델과의 차이를 짚습니다.
source: _krafton/SW_AI-W05-react/docs/class-and-structure-diagram.md
---

# React-like 런타임과 Fiber 의 구조 차이

## 문서 범위

이 문서는 직접 구현한 React-like 런타임의 실제 코드 구조를 정리하고, 그 위에서 실제 React Fiber 모델과의 설계 차이를 비교하기 위한 문서입니다.

이 런타임은 일반적인 React 애플리케이션이 아니라 `src/core` 에 직접 구현한 런타임 위에서 `src/app` 데모 앱이 동작하는 구조입니다. 명시적인 `class` 는 사실상 `FunctionComponent` 하나뿐이며, 그 외 구성 요소는 함수형 컴포넌트와 역할별 모듈 함수 두 범주로 나뉩니다.

## 상위 구조 요약

큰 흐름은 다음과 같습니다.

1. `src/app/main.js` 가 브라우저에서 앱을 시작
2. `createApp()` 이 루트 `FunctionComponent` 인스턴스를 생성
3. `FunctionComponent` 가 루트 `App` 함수를 실행
4. `App` 과 자식 함수형 컴포넌트가 `h()` 로 VNode 를 생성
5. `resolveComponentTree()` 가 자식 함수형 컴포넌트를 일반 VNode 트리로 전개
6. `createEngine()` 이 최초 DOM 렌더 또는 diff/patch 기반 DOM 갱신 수행
7. `useEffect` 로 수집된 effect 는 DOM 반영 이후 commit

## 핵심 구조 해설

### FunctionComponent 가 런타임의 중심

루트 컴포넌트의 상태 저장소, Hook 슬롯, 렌더 사이클, effect commit, unmount cleanup 은 모두 `FunctionComponent` 가 관리합니다. 실제 React 의 Fiber + 컴포넌트 인스턴스 분산 구조 대신, 이 런타임은 "루트 하나를 관리하는 런타임 관리자 클래스" 를 중심으로 설계되어 있습니다.

### App 이 모든 상태를 소유

데모 앱의 상태는 모두 `src/app/App.js` 에 있습니다. 대표 상태는 `currentPage`, `cards`, `selectedCardId`, `settings`, `searchKeyword`, `typeFilter`, `favoritesOnly`, `sortMode`, `detailById` 입니다. 페이지 컴포넌트와 공용 컴포넌트는 이 상태를 직접 가지지 않고 `props` 만 받아 렌더합니다.

### 자식 함수형 컴포넌트는 stateless renderer

`resolveComponentTree()` 는 `h(Child, props)` 형태의 자식 함수를 즉시 실행해 일반 VNode 로 바꿉니다. 이 과정에서 자식은 독립 Hook 저장소를 가지지 않으며, resolver 단계에서는 Hook 사용 자체가 금지됩니다. 자식 컴포넌트는 `props -> VNode` 를 반환하는 순수 렌더 함수에 가깝습니다.

### 엔진 계층은 diff → patch → DOM 으로 이어짐

- 최초 mount: `createDomFromVNode()` 로 DOM 전체 생성
- update: `diff()` 로 patch 목록 계산
- commit: `applyPatches()` 로 실제 DOM 변경

이 구조 덕분에 앱 계층과 DOM 반영 계층이 분리됩니다.

## Fiber 모델과의 차이

### 상태와 Hook 이 루트에만 있음

실제 React 는 각 함수형 컴포넌트가 자신의 state 와 Hook 체인을 가질 수 있습니다. 이 런타임은 루트 `App` 만 Hook 을 사용하고 자식은 Hook 을 사용할 수 없습니다. 상태 소유권이 루트 한 곳으로 강하게 제한됩니다.

코드 기준으로는 `FunctionComponent` 인스턴스가 단 하나의 `hooks[]` 배열을 소유하고, 루트 `App` 렌더 동안에만 `currentDispatcher` 가 Hook 사용을 허용합니다. 자식 함수형 컴포넌트는 `resolveComponentTree()` 에서 Hook 비허용 상태로 실행됩니다.

이 차이로 실제 React 에서 가능한 다음 패턴들이 이 런타임에서는 금지됩니다.

- 자식 컴포넌트 내부 `useState`
- 자식 컴포넌트 내부 `useEffect`
- 컴포넌트별 로컬 상태 캡슐화
- 동일 자식 컴포넌트의 여러 인스턴스가 각자 독립 상태를 갖는 구조

React 의 "state is local to each component instance" 모델이 아니라 "all state lives in the single root app" 모델을 채택합니다.

### 자식 컴포넌트가 Fiber 단위가 아님

실제 React 는 각 컴포넌트가 Fiber 노드 수준에서 추적되며 컴포넌트 경계 단위로 reconciliation 이 이뤄집니다. 이 런타임은 자식 함수형 컴포넌트를 먼저 실행해 일반 VNode 로 평탄화한 뒤 diff 를 수행합니다. diff 의 대상은 "컴포넌트 트리" 가 아니라 "해석이 끝난 VNode 트리" 입니다.

- 실제 React: 컴포넌트 경계마다 작업 단위를 가짐
- 이 런타임: 자식을 먼저 실행해 결과물 VNode 로 바꾼 뒤 비교
- 자식 컴포넌트 자체의 생명주기나 개별 인스턴스 identity 는 약함
- diff 는 함수 컴포넌트를 이해하지 않고 이미 확정된 일반 노드 구조를 비교

컴포넌트 기반 렌더링이지만, reconciliation 의 기준점은 실제 React 보다 평면적입니다.

### 스케줄러가 단순

실제 React 는 우선순위, interruptible rendering, concurrent features 같은 복잡한 스케줄링 개념을 가집니다. 이 런타임은 `sync` 또는 `microtask batching` 정도만 지원하는 단순한 업데이트 예약 방식을 씁니다.

빠진 개념은 다음과 같습니다.

- lane priority
- transition 우선순위
- render 중단과 재개
- background rendering
- time slicing
- selective hydration

상태 변경은 결국 `component.update()` 를 다시 호출하는 방향으로 이어집니다. 업데이트 모델은 명확하지만, 큰 트리에서 세밀하게 작업을 나누지는 않습니다.

### effect 모델이 단순

실제 React 는 `useEffect`, `useLayoutEffect`, Strict Mode 재실행, 개발 모드 검증 등 다양한 실행 규칙을 가집니다. 이 런타임은 렌더 중 effect 인덱스를 모았다가 DOM 반영 뒤 `commitEffects()` 에서 순서대로 실행하는 단순 모델입니다.

- `useLayoutEffect` 없음
- Strict Mode double invoke 같은 개발 검증 없음
- mount·update 시 effect 타이밍 구분이 단순
- cleanup 정책도 root 중심의 단순한 순차 처리
- effect flush 우선순위나 분할 실행 개념 없음

"effect 는 DOM 이후 실행된다" 는 핵심 개념은 보여주지만 React effect 시스템의 모든 규칙을 복제하지는 않습니다.

### 이벤트 시스템이 다름

실제 React 는 Synthetic Event 시스템과 이벤트 위임 계층을 사용합니다. 이 런타임은 patch 단계에서 DOM 노드에 직접 이벤트 핸들러를 설정하거나 제거합니다. 이벤트 추상화 계층이 얇습니다.

- 장점: 구현이 직관적이고 디버깅이 쉬움
- 장점: DOM 이벤트와 코드 연결 관계가 직접적
- 단점: React 이벤트 정규화 계층 없음
- 단점: 캡처링·버블링 추상화, SyntheticEvent 재사용 정책 없음
- 단점: 프레임워크 차원의 이벤트 최적화 여지가 작음

### 지원 범위를 의도적으로 축소

실제 React 에는 Context, Ref, Suspense, Error Boundary, Portal, SSR hydration, Concurrent rendering 같은 개념이 넓게 존재합니다. 이 런타임은 `함수형 컴포넌트 + 루트 상태 + useState/useEffect/useMemo + VDOM diff/patch` 에 집중한 축소 구현입니다.

목표는 "React 와 완전히 같은 앱 프레임워크 만들기" 가 아니라 "React 의 핵심 개념 몇 가지를 직접 구현해 설명 가능하게 만들기" 입니다.

### 상태 업데이트 전파가 직접적

실제 React 는 상태 업데이트가 Fiber 트리와 scheduler 를 거치며 어떤 서브트리를 다시 계산할지 프레임워크가 결정합니다. 이 런타임에서는 `useState` setter 가 슬롯 값을 바꾸고 `scheduleUpdate(component)` 를 호출하면 결국 루트 `FunctionComponent.update()` 가 다시 수행됩니다.

상태 변경의 전파 경로는 다음처럼 짧습니다.

1. setter 호출
2. Hook slot 값 변경
3. 루트 update 예약
4. 루트 `App` 재실행
5. 자식 함수형 컴포넌트 재전개
6. VNode diff
7. DOM patch

학습에는 좋지만, 실제 React 처럼 복잡한 부분 렌더 최적화나 다양한 우선순위 제어를 제공하지는 않습니다.

## 정리

이 런타임이 "React 를 완전히 복제" 한 것은 아닙니다. 핵심 개념이 어떻게 동작하는지를 설명 가능한 구조로 재구성한 React-like 런타임입니다. 실제 React 와의 가장 큰 차이는 "모든 상태가 루트에만 있고, 자식은 stateless renderer" 라는 점입니다. 따라서 이 구현은 범용 프레임워크라기보다 `Component + State + Hooks + VDOM + Diff + Patch` 를 분해해 보여주는 학습용 엔진에 가깝습니다.

## 다음으로 볼 키워드

- Fiber 노드와 Reconciler 내부 작업 단위
- Concurrent Rendering 과 Lane Priority
- Synthetic Event 시스템과 이벤트 위임
