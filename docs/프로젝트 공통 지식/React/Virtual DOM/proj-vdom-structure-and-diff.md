---
title: Virtual DOM 노드 구조 - ElementVNode와 TextVNode
category: 프로젝트 공통 지식
keyword: React
subkeyword: Virtual DOM
created: 2026-04-20
updated: 2026-04-20
tags: [virtual-dom, vnode, element-vnode, text-vnode, reconciliation]
summary: React-like 런타임 구현에서 화면 설명서 역할을 하는 VNode 타입 두 가지의 구조와 필드를 정리합니다.
source: _krafton/SW_AI-W04-react/docs/vdom.md
---

# Virtual DOM 노드 구조

## 개요

Virtual DOM 은 실제 DOM 을 직접 조작하기 전에 "어떤 화면이어야 하는가" 를 객체 트리로 표현하는 중간 표현입니다. 이 런타임에서는 두 종류의 노드만으로 전체 트리를 표현합니다.

```ts
type VNode = ElementVNode | TextVNode
```

element 노드는 태그와 속성, 자식 목록을 담고, text 노드는 문자열 한 덩어리를 담습니다.

## ElementVNode

태그 기반 노드입니다. `h("button", props, ...children)` 같은 호출이 최종적으로 이 구조로 정규화됩니다.

- `type`: 리터럴 `'element'`
- `tag`: 태그 이름 (예: `button`, `div`, `img`)
- `key`: 형제 목록에서 노드의 정체성을 구분하는 선택적 키 (없으면 `null`)
- `props`: 문자열 속성 맵. DOM 속성 반영에 사용합니다.
- `children`: 자식 VNode 배열

```ts
type ElementVNode = {
  type: 'element';
  tag: string;
  key: string | null;
  props: Record<string, string>;
  children: VNode[];
};
```

`key` 를 별도 필드로 분리해 두면 diff 단계에서 "같은 아이템이 이동한 것인가, 새 아이템인가" 를 판단할 수 있습니다. 리스트 렌더링의 순서가 바뀌어도 key 가 같으면 DOM 을 재사용할 수 있습니다.

## TextVNode

문자열 자식을 담는 최소 단위 노드입니다.

- `type`: 리터럴 `'text'`
- `value`: 실제 문자열 값

```ts
type TextVNode = {
  type: 'text';
  value: string;
};
```

숫자나 불리언이 자식으로 들어오면 런타임이 문자열로 정규화해 `TextVNode` 로 감쌉니다. `null`, `undefined`, `false` 같은 값은 렌더 가능한 빈 자식으로 취급해 트리에서 제외합니다.

## 두 타입만으로 충분한 이유

함수형 자식 컴포넌트는 별도 VNode 타입이 아닙니다. `h(Child, props)` 같은 선언은 resolver 단계에서 즉시 호출되어 일반 VNode 트리로 펼쳐집니다. diff 가 비교하는 대상은 이미 펼쳐진 `element` 와 `text` 두 종류뿐입니다.

덕분에 diff 알고리즘이 단순해집니다. 두 노드를 비교할 때 확인할 분기는 다음과 같습니다.

- 한쪽이 text 면 값 비교 후 `SET_TEXT` patch 생성
- 양쪽이 element 면 tag, props, events, children 순으로 비교
- tag 자체가 다르면 `REPLACE_NODE`

## 다음으로 볼 키워드

- 자식 컴포넌트 전개 단계인 `resolveComponentTree`
- 이벤트 prop 분리 규칙을 가진 `h` 함수
- diff 결과인 patch 타입 목록
