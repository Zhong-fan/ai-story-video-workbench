# Workspace Asset Thumbnail Preview Design

**Date:** 2026-05-20

**Goal:** 给工作区里的视频相关资产提供统一的小缩略预览，点击缩略图后在页面内浮窗放大查看，避免再增加跳页或独立大预览入口。

## Current State Snapshot

- 前端已经有统一的页面内预览浮窗：
  - `frontend/src/components/workspace/PreviewModal.vue`
  - `frontend/src/components/workspace/LongformPipelinePanel.vue`
- 视频工作区已经有多种资产卡片：
  - 角色三视图
  - 视觉素材
  - 分镜素材
  - 成片任务
- 后端和 store 已有参考图数据模型与审核接口，未来也可以接入同一套缩略预览，但本次设计不新增独立入口。

## User Problem

用户想要的是密集、可扫视的工作区：

- 卡片上先看到小预览，知道这是什么
- 点一下再放大查看细节
- 不要每次都打开一个全尺寸大块内容
- 不要把不同资产类型分散成不同预览逻辑

## Proposal

保留统一的 `PreviewModal`，在各个资产卡片上补一个固定尺寸的小预览区。

### Primary Placement

优先覆盖视频工作区里的资产卡片：

- 角色三视图卡
- 视觉素材卡
- 分镜素材卡
- 成片卡

如果以后参考图进入视频工作区，也使用同一套缩略预览逻辑。

### Data Flow

1. 卡片自己决定显示什么小预览。
2. 卡片把资源 URL 和类型传给共享预览弹窗。
3. 点击缩略图或预览按钮后，`PreviewModal` 在页面内放大显示。
4. 关闭后回到原位置，不改变页面路由。

## Placement Rules

- 不新增独立预览页面。
- 每个资产卡片最多保留一个小预览区，避免卡片内多层嵌套。
- 缩略预览尺寸固定，保证列表密度。
- 音频没有静态图片时，允许用小型播放器外壳或播放标识代替。
- 预览放大后复用同一个 `PreviewModal`。

## UI Behavior

### In the asset cards

展示：

- 缩略预览
- 资产类型
- 状态
- 必要时的最小操作按钮

可执行操作：

- 点击缩略图放大预览
- 保持已有的锁定、删除、审核等动作不变

### Reuse

- 放大预览统一复用 `PreviewModal.vue`
- 列表数据继续来自现有 store

## Scope

This slice only adds thumbnail previews and shared enlarge-on-click behavior for video-workspace assets.

Not included:

- 新的预览页面
- 新的资产生成逻辑
- 批量审核改造
- 资产权限模型改造

## Testing

建议最小验证：

- 源码级测试确认 `LongformPipelinePanel.vue` 继续复用 `PreviewModal`
- 源码级测试确认资产卡片存在缩略预览入口
- `npm run build` 通过

## Risks

- 音频没有天然静态缩略图，需要统一退化成小型播放入口。
- 资产卡片过多时，缩略预览可能让面板变高，需要保持固定尺寸和截断策略。
