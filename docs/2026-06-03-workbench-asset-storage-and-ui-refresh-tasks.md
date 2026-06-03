# Workbench Asset Storage and UI Refresh Tasks

Date: 2026-06-03
Status: draft task brief

## Background

This document records the next product and engineering tasks for ChenFlow Workbench after the short-drama continuity work. The main themes are:

- Make media asset deletion manageable and recoverable.
- Shorten and regularize `output/` storage paths.
- Expose stable project and asset numbers in the UI.
- Refresh the frontend visual direction so it feels intentional, user-facing, and distinctive rather than generic AI-tool UI.

## Task 1: Project-Scoped Asset Storage

### Problem

Current generated asset paths can become too long and too dependent on titles, chapter names, storyboard names, and shot paths. This makes files harder to inspect, move, recover, and reason about.

Project names can change, so project storage paths should not depend on mutable titles.

### Desired Direction

Use stable database IDs as filesystem and UI identifiers.

Filesystem project directory:

```text
output/projects/p000001/
```

Normal media asset directory:

```text
output/projects/p000001/assets/media/m000123/
```

Deleted media asset directory:

```text
output/projects/p000001/deleted/media/m000123/
```

Frontend display IDs:

```text
Project.id    -> P000001
MediaAsset.id -> M000123
```

The filesystem should use lowercase prefixes (`p000001`, `m000123`), while the frontend should show uppercase product-style labels (`P000001`, `M000123`).

### First Slice

- Do not perform a full historical migration of all existing files in the first slice.
- New or restored media assets should move toward the short project-scoped path.
- Deleting an old asset should move it into the new project-scoped `deleted/` path even if the old source path was long.
- Restoring an old asset may restore it into the new short `assets/` path rather than the original long path.
- Store original and moved paths in `MediaAsset.meta_json` for traceability.

Suggested metadata:

```json
{
  "original_uri": "output/projects/old-long-path/file.png",
  "deleted_uri": "output/projects/p000001/deleted/media/m000123/file.png",
  "restored_uri": "output/projects/p000001/assets/media/m000123/file.png"
}
```

## Task 2: MediaAsset Recycle Bin

### Problem

The current recycle bin supports projects, novels, character cards, and dirty evolution records. `MediaAsset` deletion currently removes the database row directly and does not place the asset in the recycle bin.

This is not good enough for generated images, first frames, last frames, character turnarounds, audio, and videos, because users need to review, restore, and permanently manage deleted media.

### Desired Behavior

When a user deletes a `MediaAsset`:

1. Do not hard-delete the row.
2. Set `MediaAsset.deleted_at`.
3. Move the underlying file, if present, into:

```text
output/projects/p000001/deleted/media/m000123/
```

4. Update `MediaAsset.uri` to the deleted path.
5. Preserve the previous path in `meta_json`.
6. Add the asset to the recycle bin as item type `media_asset`.

When a user restores a deleted `MediaAsset`:

1. Move the file back to:

```text
output/projects/p000001/assets/media/m000123/
```

2. Update `MediaAsset.uri`.
3. Clear `MediaAsset.deleted_at`.
4. Keep trace metadata in `meta_json`.

### Error Handling

- If delete is requested and the source file exists but cannot be moved, return an error and do not mutate the database.
- If delete is requested and the source file is already missing, still allow the asset to enter the recycle bin and mark metadata with `file_missing: true`.
- If restore is requested and the deleted file is missing, restore the database record but keep `file_missing: true` so the UI can show that the file itself is unavailable.

### UI Requirements

Recycle bin media asset cards should show:

- Asset code, for example `M000123`
- Asset type, for example `shot_first_frame`, `shot_last_frame`, `character_turnaround`, `video`, `voice`
- Parent project code, for example `P000001`
- Parent project title
- Deleted time
- Restore action

## Task 3: Visible Numbering in the Frontend

### Problem

Users need a stable way to connect UI items to filesystem folders, database rows, logs, and debugging conversations.

### Desired Behavior

Show stable IDs in the UI:

- Project cards: `P000001`
- Project detail header: `P000001 · Project title`
- Media asset cards: `M000123`
- Recycle bin cards: `M000123 · shot_first_frame`, with project context

Implementation should use formatting helpers rather than new database fields.

Example:

```text
Project.id -> P000001
MediaAsset.id -> M000123
```

## Task 4: Frontend Visual Refresh

### User Feedback

The current frontend visual direction is not good enough after recent changes:

- The floating transparent background blocks are visually appealing, but their movement is too subtle and has little presence.
- The floating shapes are too uniform.
- The overall page feels ugly after recent changes.
- The product feels too obviously AI-generated.
- It does not feel fresh, memorable, or user-facing.
- Many labels and descriptions feel strange or internal rather than written for real users.

### Desired Direction

Keep and improve the translucent floating-shape background idea, but make it more deliberate and visually present.

Improve:

- Movement amplitude and timing
- Variety of shapes
- Layering and transparency
- Visual rhythm across desktop and mobile
- Overall product personality
- User-facing wording
- Page hierarchy and navigation clarity

Avoid:

- Generic AI SaaS visual language
- Decorative elements that are too faint to matter
- Repetitive single-shape backgrounds
- Internal system phrasing in user-facing UI
- Over-explaining features inside the page
- Dense, awkward, or machine-like Chinese copy

### Visual Requirements

The background should continue to use floating transparent shapes, but with more presence:

- Larger movement range
- Multiple shape types, not just similar rounded blocks
- Different sizes and depth layers
- Slow but noticeable motion
- No layout overlap or readability loss
- Motion should feel ambient, not distracting

Possible shape families:

- Frosted rounded panels
- Thin glass rings
- Soft translucent strips
- Small luminous tiles
- Subtle beveled chips
- Irregular glass shards, if tasteful and restrained

### Copywriting Requirements

Rewrite visible labels and explanatory text so they sound like a real creative tool for users, not like internal implementation notes.

Examples of direction:

- Prefer clear action words.
- Prefer user intent over system mechanics.
- Avoid awkward AI wording.
- Avoid long descriptions inside compact cards.
- Keep Chinese concise, specific, and natural.

## Task 5: Implementation Constraints

- Keep the first storage slice focused on `MediaAsset`.
- Do not build a full asset lifecycle platform yet.
- Do not run a risky full historical file migration in the first implementation unless explicitly approved.
- Keep old paths readable and restorable.
- Use tests before implementation for deletion, restore, missing file handling, and recycle bin output.
- Frontend visual changes must be verified with Playwright screenshots across desktop and mobile.

## Open Decisions

- Whether to later migrate all historical assets into short paths.
- Whether `ReferenceImageAsset` should join the same recycle bin model in a later slice.
- Whether permanent delete should be added immediately or after recycle-bin restore is stable.
- Whether the frontend refresh should be a single pass or split by shell, workspace home, project detail, asset library, and video stage.
