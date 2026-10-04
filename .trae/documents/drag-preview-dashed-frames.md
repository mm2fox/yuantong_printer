# 预览虚线框拖拽调整方案

## 背景

当前模板编辑器中，姓名区域和阳上区域的位置和大小只能通过左侧表单的滑块调节。用户希望能在预览中直接拖动虚线框来调整位置，自动更新对应的百分比值，实现所见即所得的交互体验。

## 修改范围

仅修改 `frontend/src/components/TemplateEditor.vue`（模板 + 脚本 + 样式）。TemplateList.vue 和 PrintPreviewDialog.vue 是只读预览，不改动。

## 实现方案

### 1. 移动手柄：capacity-badge

复用已有的容量徽章（`capacity-badge`）作为移动手柄：
- 徽章位于 `top: -20px`，在区域内容框之外，不会与 `contenteditable` 单元格冲突
- CSS：`pointer-events: none` → `auto`，添加 `cursor: move; user-select: none;`
- 模板：`@mousedown.stop.prevent="startDrag($event, 'name', 'move')"`

### 2. 缩放手柄：右下角圆点

每个区域添加一个 12px 圆形手柄（`.resize-handle`），位于右下角外侧：
- 默认 `opacity: 0`，区域 hover 时显示
- `cursor: nwse-resize`，拖拽更新 width + height
- 姓名区域红色边框，阳上区域绿色边框

### 3. 拖拽逻辑

**坐标转换**：通过 `previewContentRef` 的 `getBoundingClientRect()` 获取屏幕实际尺寸，自动处理缩放：
```
dxPct = dxScreenPx / rect.width * 100
dyPct = dyScreenPx / rect.height * 100
```

**约束值**（与滑块一致）：
- top/left: 0–80
- width/height: 10–100
- top + height ≤ 100, left + width ≤ 100

**精度**：四舍五入到 1 位小数，与滑块输入框兼容

**翻转模式**：`flipH || flipV` 时禁止拖拽，提示用户先关闭翻转

**printOffsetY**：拖拽更新 `namesTopPct` 基础值（偏移量在渲染时加，不影响 delta 计算）

### 4. 具体代码改动

#### import（第 454 行）
```js
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
```

#### 模板 ref（第 335 行）
```html
<div class="preview-content" ref="previewContentRef" :style="...">
```

#### 徽章添加 mousedown（第 337、347 行）
```html
<span class="capacity-badge" :style="{ background: '#67c23a' }"
      @mousedown.stop.prevent="startDrag($event, 'yangshang', 'move')">
```
```html
<span class="capacity-badge" :style="{ background: '#f56c6c' }"
      @mousedown.stop.prevent="startDrag($event, 'name', 'move')">
```

#### 缩放手柄（阳上区域 `+ 添加` 按钮后、姓名区域 `+ 添加` 按钮后）
```html
<div class="resize-handle" @mousedown.stop.prevent="startDrag($event, 'yangshang', 'resize')"></div>
<div class="resize-handle" @mousedown.stop.prevent="startDrag($event, 'name', 'resize')"></div>
```

#### 脚本：状态和函数（第 814 行后）
- `previewContentRef` ref
- `AREA_FIELDS` 映射表（name/yangshang → 字段名）
- `dragState` ref（null 或 { area, type, startX, startY, startValues, fields, contentRect }）
- `startDrag(e, area, type)`：检查翻转、获取 rect、记录起始值
- `onDragMove(e)`：计算 delta 百分比、约束、更新 layoutConfig
- `onDragEnd()`：清空 dragState

#### 生命周期（watch 附近）
```js
onMounted(() => {
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
})
```

#### z-index 调整（getNamesAreaStyle / getYangshangAreaStyle）
- 姓名区域: `zIndex: 1`
- 阳上区域: `zIndex: 2`（更小，需要在重叠时浮于上层）

#### CSS（第 1281 行后）
```css
.capacity-badge { pointer-events: auto; cursor: move; user-select: none; }
.resize-handle { position: absolute; right: -5px; bottom: -5px; width: 12px; height: 12px;
  background: #fff; border: 2px solid #f56c6c; border-radius: 50%; cursor: nwse-resize;
  z-index: 20; pointer-events: auto; box-sizing: border-box; opacity: 0; transition: opacity 0.15s; }
.preview-yangshang-area .resize-handle { border-color: #67c23a; }
.preview-names-area:hover .resize-handle,
.preview-yangshang-area:hover .resize-handle { opacity: 1; }
```

## 验证

1. `npm run build` 构建通过
2. 打开编辑器，拖动姓名徽章 → 区域移动，滑块同步更新
3. 拖动阳上徽章 → 独立移动，不影响姓名区域
4. 拖动右下角手柄 → 宽高调整，左上角锚定不动
5. 拖到边界 → 约束生效，不超出页面
6. 翻转模式 → 提示不可拖拽
7. 编辑文字 → 不触发拖拽
8. 关闭再打开编辑器 → 无重复监听器
