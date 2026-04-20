---
title: 업데이트 흐름과 microtask 배칭 스케줄링
category: 프로젝트 공통 지식
keyword: React
subkeyword: Fiber 아키텍처
created: 2026-04-20
updated: 2026-04-20
tags: [scheduling, microtask, batching, set-state, concurrent-rendering, fiber]
summary: React-like 런타임의 sync·microtask 두 모드가 setState 이후 실제로 어떤 순서로 update 를 수행하는지 정리합니다.
source: _krafton/SW_AI-W05-react/docs/update-flow-and-scheduling.md
---

# 업데이트 흐름과 스케줄링

## 이 문서가 답하는 질문

직접 구현한 React-like 런타임에서 상태 업데이트가 어떤 순서로 처리되는지, 그리고 `sync` 와 `microtask batching` 이 실제로 무엇을 제어하는지 설명합니다. 특히 다음 질문에 답하는 것을 목표로 합니다.

- `setState` 이후 어떤 함수가 어떤 순서로 호출되는가
- `queueMicrotask()` 는 왜 사용되는가
- 이 구현이 작업을 나눠 처리하는가, 아니면 시작 시점만 미루는가
- 실제 React 의 스케줄링과 무엇이 다른가

## 결론 요약

현재 구현은 상태 업데이트를 다음 전략으로 처리합니다.

- `sync` 모드: `setState` 직후 즉시 `update()` 실행
- `microtask` 모드: `setState` 직후 즉시 실행하지 않고, 현재 동기 코드가 끝난 뒤 `update()` 를 한 번 실행

중요한 점은 다음과 같습니다.

- `microtask` 는 업데이트의 **시작 시점** 을 조금 늦춥니다.
- 하지만 업데이트 작업 자체를 여러 조각으로 **쪼개지는 않습니다**.
- 한 번 `update()` 가 시작되면 `render → diff → patch → commit` 을 한 흐름으로 끝까지 수행합니다.

"비동기로 예약은 하지만 concurrent rendering 처럼 작업 단위를 세분화하지는 않는 구조" 입니다.

## queueMicrotask() 가 적절한 이유

`queueMicrotask(callback)` 은 callback 을 microtask queue 에 넣습니다. 의미는 다음과 같습니다.

- 지금 실행 중인 함수는 끝까지 실행
- 현재 클릭 핸들러 같은 동기 코드도 끝까지 실행
- 그 직후 microtask queue 를 비우면서 callback 실행

즉 "아주 잠깐 뒤" 로 실행을 미루는 도구입니다.

이 런타임에서 이것이 적절한 이유는 다음과 같습니다.

- 같은 클릭 핸들러 안에서 여러 `setState` 가 연달아 호출될 수 있음
- 매번 즉시 `update()` 를 돌리면 불필요한 중복 렌더 발생
- microtask 로 미루면 현재 핸들러가 끝난 뒤 상태 변경 결과를 한 번에 반영

예시는 다음과 같습니다.

```js
setSelectedCardId(cardId);
setCurrentPage("detail");
```

같은 동기 구간 안에서 두 setter 가 호출되면 microtask batching 은 두 상태 변경을 한 번의 `update()` 로 합칩니다.

## 작업 분할은 아닙니다

이 부분이 핵심 포인트입니다. 현재 구현은 callback 으로 업데이트 시작을 늦추기는 하지만, 작업 단위를 쪼개거나 중간에 양보하지 않습니다.

- `queueMicrotask()` 는 `update()` 호출 시점만 제어합니다.
- `update()` 가 시작되면 내부 작업은 한 번에 진행됩니다.

`update()` 가 한 흐름으로 수행하는 단계는 다음과 같습니다.

1. 루트 `App` 재실행
2. 자식 함수형 컴포넌트 전개
3. 새 VNode 생성
4. 이전 VNode 와 diff
5. patch 적용
6. effect commit

"비동기 예약" 은 있지만 "작업 분할형 스케줄링" 은 아닙니다.

## 전체 업데이트 순서도

실제 호출 순서 기준 ASCII 순서도입니다.

```text
[사용자 클릭]
   |
   v
[브라우저가 DOM 이벤트 핸들러 실행]
   |
   v
[핸들러 내부에서 setState 호출]
   |
   v
[useState setter]
   |-- 이전 값과 같으면 종료
   |-- 값이 다르면 hook slot.value 갱신
   v
[scheduleUpdate(component)]
   |-- component.isMounted 아니면 종료
   |-- batching === "sync" ?
   |      +-- yes --> [component.update() 즉시 실행]
   |-- batching === "microtask"
          |-- 이미 scheduledUpdate 있음 --> 종료
          |-- 없으면 token 저장
          |-- queueMicrotask(() => flushScheduledUpdate(...))
          v
   [현재 클릭 핸들러 종료]
          v
   [microtask queue flush]
          v
   [flushScheduledUpdate(component, token)]
          |-- 취소됐거나 unmount 면 종료
          +-- component.update()
                    v
             [performRender()]
                    |-- 루트 App 다시 실행
                    |-- 자식 함수 컴포넌트 전개
                    |-- 새 VNode 생성
                    v
             [engine.patch(nextVNode)]
                    |-- diff(oldVNode, nextVNode)
                    |-- applyPatches(dom, patches)
                    v
             [commitEffects()]
                    v
             [업데이트 완료]
```

## sync 와 microtask 의 차이

같은 동기 구간에 다음 코드가 있다고 해 봅시다.

```js
setA(1);
setB(2);
setC(3);
```

### sync 모드

```text
setA -> update()
setB -> update()
setC -> update()
```

매 상태 변경마다 update 가 호출될 수 있습니다.

### microtask 모드

```text
setA -> update 예약
setB -> 이미 예약 있음, 추가 예약 없음
setC -> 이미 예약 있음, 추가 예약 없음
현재 동기 코드 종료
-> microtask 에서 update() 1 번 실행
```

같은 동기 구간의 여러 상태 변경을 하나의 update 로 묶습니다.

## 현재 앱의 선택

브라우저 데모 앱은 `microtask` 모드로 동작합니다. `sync` 모드도 구현되어 있지만 실제 엔트리에서는 microtask 를 사용합니다.

## batching 의 의미

이 런타임에서 `batching` 은 다음 의미로 쓰입니다.

- 여러 상태 변경을
- 여러 번 즉시 렌더하지 않고
- 한 번의 `update()` 로 합치는 것

다만 이 batching 은 매우 단순합니다.

- 같은 동기 구간의 중복 update 를 줄이는 수준
- 우선순위 없음
- 작업 중단·재개 없음
- 큰 트리의 부분 렌더 없음

"중복 업데이트 방지용 batching" 에 가깝습니다.

## 실제 React 와의 차이

실제 React 는 상태 업데이트 이후 내부적으로 훨씬 더 많은 일을 합니다.

- update 를 Fiber 트리에 등록
- 우선순위 계산
- 작업을 쪼갤 수 있음
- 중간에 yield 하거나 나중에 이어서 할 수 있음
- concurrent rendering 모델 지원

현재 구현은 다음 흐름에 더 가깝습니다.

```text
상태 변경
-> update 예약 여부 결정
-> 루트 App 전체 재계산
-> diff
-> patch
-> commit
```

업데이트 시작 시점은 제어하지만, 시작한 뒤의 작업은 일렬로 끝까지 수행합니다.

## 요약

현재 런타임은 `queueMicrotask()` 를 이용해 여러 상태 변경을 한 번의 `update()` 로 묶을 수 있지만, 실제 React 처럼 렌더 작업 자체를 잘게 나누고 우선순위에 따라 스케줄링하지는 않습니다.

## 다음으로 볼 키워드

- Fiber Lane Priority 와 Concurrent Rendering
- Suspense 와 Transition 우선순위
- `queueMicrotask` 와 macrotask 큐의 차이
