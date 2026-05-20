# Workspace Preview Modal Design

**Date:** 2026-05-20

**Goal:** 把工作区里分散的图片、音频、视频预览统一成一个页面内浮窗，减少跳转和重复实现，让素材、分镜、成片都能在同一套预览组件里打开。

## Current State Snapshot

- `LongformPipelinePanel.vue` 里已经有本地 `preview` 状态和一个页面内浮层。
- 当前预览逻辑散在组件内部，主要是：
  - 图片预览
  - 音频试听
  - 视频预览
- 预览遮罩和容器样式已经存在于 `frontend/src/styles/workspace.css`：
  - `.asset-modal`
  - `.asset-modal__body`
  - `.asset-preview`
- 目前没有统一的预览组件，其他工作区组件如果要预览，也要自己处理状态和展示逻辑。

## User Problem

现在的预览体验有三个问题：

1. 预览能力分散在各个组件里，维护成本高。
2. 预览打开后和业务卡片耦合太紧，不方便复用到参考图、素材、成片等不同区域。
3. 用户希望是“前端页面里的小窗口”，而不是跳页或新窗口。

## Proposal

做一个统一的页面内预览浮窗组件，作为所有工作区预览入口的共同展示层。

### Component Boundary

新增一个通用组件，例如：

- `frontend/src/components/workspace/PreviewModal.vue`

职责：

- 接收 `open / title / kind / url`
- 按 `kind` 渲染 `img`、`audio`、`video`
- 提供关闭按钮、遮罩点击关闭、ESC 关闭
- 不负责判断业务类型，不负责决定何时打开

业务组件只负责：

- 生成预览数据
- 传入 `PreviewModal`
- 在卡片上调用统一的 `openPreview(...)`

### Data Flow

1. 用户在素材卡、成片卡、参考图卡上点“预览”。
2. 业务组件把资源信息写入统一预览状态。
3. `PreviewModal` 在页面内弹出。
4. 用户关闭后，状态清空，回到原页面。

### Scope

先覆盖工作区里已有的三类内容：

- 图片
- 音频
- 视频

优先接入：

- 视觉素材
- 分镜首帧
- 分镜素材
- 成片任务

不扩展到：

- 新页面
- 新路由
- 浏览器新标签页

## UX Rules

- 预览必须在当前页面内完成。
- 图片默认居中显示，保持原比例。
- 视频和音频使用原生播放器。
- 浮窗优先保证内容可看清，不追求装饰性。
- 遮罩点击和 ESC 都应关闭。
- 关闭后保留用户原本滚动位置和页面状态。

## Implementation Notes

- 复用现有 `.asset-modal` / `.asset-modal__body` / `.asset-preview` 样式，必要时再拆成更通用的预览样式。
- 如果多个组件都需要预览，统一把预览状态提升到工作区公共层，而不是每个组件单独维护一套。
- 预览 title 保持简短，直接显示资源类型和状态即可。

## Testing

建议最小验证：

- 前端模板检查通过。
- `npm run build` 通过。
- 现有 workspace 相关单测不回退。
- 如有必要，再补一个源代码级测试，确认预览组件被统一复用。

## Non-goals

- 不做独立预览页面。
- 不做复杂的批注、缩放、对比模式。
- 不做拖拽调整大小，除非后续明确需要。
- 不改动资源生成逻辑，只改预览展示层。
