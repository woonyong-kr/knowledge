---
title: React-like 런타임 공개 API 계약
category: 프로젝트 공통 지식
keyword: React
created: 2026-04-20
updated: 2026-04-20
tags: [public-api, function-component, create-app, hooks, dom-events, form-semantics]
summary: 자체 구현한 React-like 런타임이 외부와 공유하는 공개 API 의 시그니처와 동작 계약을 정리합니다.
source: _krafton/SW_AI-W05-react/docs/api-spec.md
---

# React-like 런타임 공개 API 계약

## 공개 API 의 축

공개 엔트리포인트는 `src/index.js` 이며, 외부에서 사용할 API 는 다음 여섯 축으로 구성됩니다.

- `FunctionComponent`
- `createApp`
- `h`
- `useState`, `useEffect`, `useMemo`

이 계약의 목표는 실제 React 와의 1:1 호환이 아니라, Hook·VDOM·Diff·Patch 를 설명 가능하게 노출하는 최소 API 집합입니다.

## FunctionComponent

루트 함수형 컴포넌트를 감싸는 런타임 클래스입니다. Hook 저장소와 렌더 사이클 제어를 모두 담당합니다.

### 생성자

```js
new FunctionComponent(renderFn, options?)
```

- `renderFn: (props) => VNode`
- `options?: { name?: string, batching?: "sync" | "microtask" }`

인스턴스는 `hooks` 배열과 `mount()`, `update()`, `unmount()` 메서드를 제공하고, 현재 props·VNode·mount 여부를 추적합니다. 내부적으로 최소 다음 속성을 유지합니다.

- `hooks`, `hookCursor`
- `currentProps`, `currentVNode`
- `rootElement`, `isMounted`

### mount

```js
component.mount({ root, props? })
```

동작은 다음과 같습니다.

- 루트 DOM 컨테이너 저장
- 루트 렌더를 최초 1 회 수행
- 생성된 VDOM 을 DOM 으로 변환해 부착
- 이후 필요한 effect 를 commit 단계에서 실행

반환값은 현재 렌더된 `VNode` 입니다.

### update

```js
component.update(nextProps?)
```

- `nextProps` 가 주어지면 기존 props 를 완전 교체
- `hookCursor` 를 0 으로 초기화
- 루트 렌더 함수를 다시 실행
- 이전 VDOM 과 다음 VDOM 을 diff
- patch 를 DOM 에 반영
- 이전 effect cleanup 과 새 effect commit 수행

반환값은 `{ vnode, patches }` 입니다.

### unmount

```js
component.unmount()
```

- 등록된 effect cleanup 을 모두 실행
- 루트 DOM 정리
- Hook dispatcher 와 내부 참조 해제
- 이후 같은 인스턴스에서 Hook update 가 다시 일어나지 않도록 차단

## createApp

`createApp` 은 앱에서 사용할 간단한 진입점입니다. 내부적으로 `FunctionComponent` 와 기존 engine 계층을 연결합니다.

### 시그니처

```js
createApp({
  root,
  component,
  props = {},
  batching = "sync",
  diffMode = "auto",
  historyLimit = null,
})
```

옵션은 목적별로 이렇게 나뉩니다.

- 필수: `root`, `component`
- 일반 선택: `props`, `batching`
- 개발용 선택: `diffMode`, `historyLimit`

### 반환

```js
{
  mount,
  unmount,
  updateProps,
  getComponent,
  inspect?,
}
```

- `mount()`: 최초 mount 수행
- `unmount()`: cleanup 실행 후 루트 종료
- `updateProps(nextProps)`: 외부 props 를 완전 교체한 뒤 재렌더
- `getComponent()`: 내부 `FunctionComponent` 인스턴스 반환
- `inspect()`: 선택 기능. 현재 상태·VNode·마지막 patch 를 반환

### 통합 규칙

- 앱은 `src/index.js` 를 통해 `createApp()` 을 사용해야 합니다.
- 내부 `src/core/...` 경로는 직접 import 하지 않습니다.
- `root` 가 유효한 Element 가 아니면 명시적 오류를 발생시킵니다.
- 같은 인스턴스 재사용은 권장하지 않습니다. `unmount()` 후 재 mount 정책은 구현에서 명시해야 합니다.
- 여러 화면은 루트 상태 전환으로 구현합니다. 추가 `createApp()` 인스턴스를 만들지 않습니다.

## h

선언형 VNode 생성 함수입니다. 기존 `src/core/vnode/h.js` 의 계약을 따릅니다.

```js
h(type, props, ...children)
```

- `type`: 문자열 태그 또는 자식 stateless component 함수
- `props`: 일반 속성, 이벤트, `key` 를 포함할 수 있음
- `children`: 문자열·숫자·VNode·배열·nullish 값의 조합

동작 규칙은 다음과 같습니다.

- `key` 를 일반 props 와 분리해 저장
- `onClick`, `onInput` 같은 함수형 이벤트 prop 을 이벤트 맵으로 분리
- 배열 children 은 평탄화·정규화
- `null`, `undefined`, `false` 는 빈 자식으로 취급
- 자식 함수형 컴포넌트는 Hook 을 사용하지 않는 pure function
- 자식 함수형 컴포넌트는 resolver 단계에서 즉시 호출되어 일반 VNode 로 전개

## useState

```js
const [state, setState] = useState(initialState)
```

- 최초 렌더에서만 초기값을 계산하고 이후에는 기존 슬롯 값을 재사용합니다.
- `setState(next)` 는 값 또는 updater function 을 받습니다.
- 상태가 달라지면 루트 update 를 예약합니다.
- `unmount` 이후 setter 호출은 no-op 이며 새 렌더나 DOM patch 를 만들지 않습니다.

제약은 다음과 같습니다.

- 루트 `FunctionComponent` 의 렌더 중에만 호출
- 자식 컴포넌트 내부에서 호출 금지
- Hook 순서가 달라지면 오류
- 활성 dispatcher 가 없으면 오류

## useEffect

```js
useEffect(create, deps?)
```

- effect 본문은 DOM patch 완료 후 실행합니다.
- `deps` 없음: 매 update 마다 실행
- `deps` 가 빈 배열: mount 후 한 번만 실행
- `deps` 가 있음: shallow compare 결과가 달라질 때만 실행
- 이전 cleanup 이 있으면 새 effect 전에 먼저 실행
- unmount 시 cleanup 실행

## useMemo

```js
const value = useMemo(factory, deps)
```

- 최초 렌더 시 값을 계산합니다.
- dependency 가 같으면 이전 값을 재사용합니다.
- dependency 가 바뀌면 다시 계산합니다.

## Hook 사용 규칙

모든 Hook 은 다음 규칙을 따릅니다.

- 루트 컴포넌트 본문에서만 호출
- 조건문·반복문 내부 호출 금지
- 이벤트 핸들러 내부 직접 호출 금지
- 호출 순서는 모든 렌더에서 동일해야 함

규칙 위반 시 명시적 오류를 발생시켜야 합니다.

## 자식 컴포넌트 계약

```js
function Child(props) {
  return h("div", null, props.label);
}
```

- 자식은 순수 함수
- 자식은 `props` 만 입력으로 받음
- 자식은 Hook 과 상태를 사용하지 않음
- 자식은 부수 효과를 직접 수행하지 않음

## 이벤트와 폼 계약

브라우저 데모에 필요한 기본 이벤트는 다음과 같습니다.

- `onClick`, `onInput`, `onChange`, `onSubmit`, `onKeydown`, `onFocus`, `onBlur`

기본 form semantics 보장 범위는 다음과 같습니다.

- text input 의 `value`
- checkbox input 의 `checked`
- textarea 의 `value`
- select 의 `value`
- `onInput` 과 `onChange` 를 통한 상태 반영

## resolveComponentTree 계약

구현은 자식 함수형 컴포넌트를 위한 전개 단계를 가집니다.

```js
resolveComponentTree(inputVNode) => resolvedVNode
```

이 단계의 보장은 다음과 같습니다.

- 함수형 자식 컴포넌트 감지
- `props` 주입 후 함수 실행
- 반환값을 일반 VNode 구조로 정규화
- 자식에서 Hook 사용이 감지되면 명시적 오류

## inspect 계약 (선택)

개발과 발표 편의를 위해 다음 정보를 권장 범위로 노출할 수 있습니다.

```js
inspect() => {
  hooks,
  currentVNode,
  lastPatches,
  renderCount,
}
```

기본 구현에서 생략할 수 있는 보조 API 입니다.

## 브라우저 부트스트랩 계약

```js
import { createApp } from "../index.js";
```

- 엔트리 파일은 `src/app/main.js`
- HTML 셸 파일은 `index.html`
- 기본 root selector 는 `#app`
- `document.getElementById("app")` 가 `null` 이면 명시적 오류
- 문서가 이미 로드된 상태면 즉시 mount, 아니면 `DOMContentLoaded` 이후 mount
- 여러 화면은 라우터 없이 상태 기반 전환으로 구현
- 페이지 전환은 별도 root mount 가 아니라 같은 루트 컴포넌트의 재렌더로 처리

## 비범위 API

이 런타임은 다음 React 계열 API 를 제공하지 않습니다.

- `useReducer`, `useContext`, `useRef`, `useCallback`
- `memo`, `forwardRef`
- `createContext`, `createPortal`
- `hydrateRoot`, `renderToString`

## 사용 예시

```js
import { createApp, h, useEffect, useMemo, useState } from "./src/index.js";

function CounterView(props) {
  return h("button", { onClick: props.onIncrement }, `count: ${props.count}`);
}

function App() {
  const [count, setCount] = useState(0);
  const doubled = useMemo(() => count * 2, [count]);

  useEffect(() => {
    document.title = `count: ${count}`;
    return () => { document.title = "cleanup"; };
  }, [count]);

  return h("section", null,
    h("h1", null, "React-like"),
    h(CounterView, {
      count,
      onIncrement: () => setCount((prev) => prev + 1),
    }),
    h("p", null, `doubled: ${doubled}`)
  );
}

createApp({
  root: document.getElementById("app"),
  component: App,
}).mount();
```

## 다음으로 볼 키워드

- 아키텍처 전체 구조
- update 흐름과 batching 스케줄링
- 자식 컴포넌트 전개 단계의 resolver 설계
