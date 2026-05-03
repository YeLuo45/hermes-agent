---
name: react-usememo-date-mutation
description: React useMemo 返回 Date 对象时的 mutation 陷阱 — 当 Date setter 方法修改了 useMemo 缓存的原始对象，导致计算结果错误。症状：数值随渲染递减、位置跳动、NaN。
trigger: useMemo 中计算日期差值、偏移量，且回调中调用了 Date.prototype setter 方法（setHours/setDate/setMonth 等）
---

# React useMemo Date Mutation 陷阱

## 问题

当 `useMemo` 返回一个 Date 对象，在组件回调中直接调用其 setter 方法（如 `date.setHours(0,0,0,0)`），会修改 useMemo 缓存的原始对象。下一次渲染时，useMemo 不会重新执行（因为依赖数组没变），但原始 Date 已经被修改，导致所有基于该 Date 的计算都出错。

## 症状

- 日期偏移量随每次渲染变化（比如应该是 0 的地方变成 -1、-2...）
- 时间线组件中任务条位置跳动
- 拖拽交互后位置计算错误
- `NaN` 出现在时间计算中

## 错误模式

```js
// ❌ 错误：dateOffset 回调内部调用了 timelineStart.setHours()
// 这会修改 useMemo 缓存的 Date 对象
const dateOffset = useCallback((date) => {
  const d = new Date(date); d.setHours(0,0,0,0);
  return Math.floor((d - new Date(timelineStart.setHours(0,0,0,0))) / 86400000);
}, [timelineStart]); // timelineStart 是 useMemo 返回的 Date

// ❌ 错误：直接修改 useMemo 返回的数组
const sorted = useMemo(() => {
  const arr = [...originalArray];
  arr.sort((a,b) => a - b); // 没问题，但如果是 arr.push() 则有问题
  return arr;
}, [originalArray]);

// ❌ 错误：在回调中修改 useMemo 返回的 Date
const handleDrag = (e) => {
  const dx = e.clientX - startX;
  timelineStart.setDate(timelineStart.getDate() + delta); // 污染 useMemo 缓存！
};
```

## 正确模式

```js
// ✅ 正确：先获取原始值的时间戳（数值），后续计算全部基于数值
const timelineStartMs = timelineStart.getTime(); // 在 useMemo 之后、回调定义之前获取
const dateOffset = useCallback((date) => {
  const d = new Date(date); d.setHours(0,0,0,0);
  return Math.floor((d.getTime() - timelineStartMs) / 86400000);
}, [timelineStartMs]); // 依赖数值而非 Date 对象

// ✅ 正确：永远不对 useMemo 返回的 Date 调用 setter
// 在需要修改日期时，创建新的 Date 实例
const newDate = new Date(originalDate);
newDate.setHours(0,0,0,0);
```

## 调试方法

1. 在 useMemo 末尾加 `console.log('computed', dateObj)` 确认 useMemo 何时重新计算
2. 在回调中 `console.log('timelineStart after mutation:', timelineStart.getTime())` 观察值是否变化
3. 如果值在每次渲染后变化（比如递减），说明发生了 mutation

## 修复步骤

1. 找到所有对 useMemo 返回 Date/Array 调用 setter/push/splice 的地方
2. 改用 `.getTime()` 获取数值，依赖数组中放数值而非对象引用
3. 如果必须用对象，使用 `useRef` 存储可变值，或在 useMemo 中 `return { ...obj }` 创建新对象
