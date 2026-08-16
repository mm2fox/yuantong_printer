<template>
  <div class="template-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>打印模板管理</span>
          <el-button type="primary" @click="handleAdd">新增模板</el-button>
        </div>
      </template>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="模板名称" label="模板名称" min-width="150">
          <template #default="{ row }">
            {{ row.模板名称 }}
            <el-tag v-if="row.是否默认 === 1" type="warning" size="small" style="margin-left: 5px">默认</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="模板类型" label="模板类型" width="120" />
        <el-table-column prop="牌位类型" label="牌位类型" width="100">
          <template #default="{ row }">{{ row.牌位类型 || '-' }}</template>
        </el-table-column>
        <el-table-column prop="是否启用" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.是否启用 === 1 ? 'success' : 'info'">{{ row.是否启用 === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="备注" label="备注" min-width="150">
          <template #default="{ row }">{{ row.备注 || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)" :disabled="row.是否默认 === 1">编辑</el-button>
            <el-button type="success" link @click="handlePreviewFromList(row)">预览</el-button>
            <el-button type="warning" link @click="handleSetDefault(row)" :disabled="row.是否默认 === 1">设为默认</el-button>
            <el-button type="info" link @click="handleCopy(row)">复制</el-button>
            <el-button type="danger" link @click="handleDelete(row)" :disabled="row.是否默认 === 1">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <TemplateEditor
      v-model:visible="editorVisible"
      :template="editingTemplate"
      :copy-mode="editorCopyMode"
      @saved="onEditorSaved"
    />

    <el-dialog v-model="previewVisible" title="打印预览" width="800px" destroy-on-close class="preview-dialog">
      <div class="preview-toolbar">
        <span class="preview-info">
          {{ previewFormData.模板名称 || '未命名模板' }} · {{ previewLayoutConfig.pageWidth }}mm × {{ previewLayoutConfig.pageHeight }}mm
        </span>
        <div class="zoom-control">
          <el-button size="small" @click="previewDialogShowRuler = !previewDialogShowRuler" :type="previewDialogShowRuler ? 'warning' : ''">标尺</el-button>
          <span class="zoom-value">X:{{ (calScaleX * 100).toFixed(0) }}% Y:{{ (calScaleY * 100).toFixed(0) }}%</span>
        </div>
        <el-button type="primary" size="small" @click="handlePrintPreviewFromDialog">打印</el-button>
      </div>
      <div class="preview-container">
        <div class="preview-page-wrapper" :style="previewWrapperStyleForDialog">
          <div class="preview-page" :style="previewPageStyleForDialog">
            <div class="small-paper-indicator" :style="dialogSmallPaperIndicatorStyle"></div>
            <div class="preview-scaler" :style="previewScalerStyleForDialog">
              <img v-if="previewLayoutConfig.backgroundImage" :src="previewLayoutConfig.backgroundImage" class="preview-bg-image" :style="{ opacity: previewLayoutConfig.backgroundOpacity / 100 }" />
              <div class="preview-content" :style="{ fontFamily: previewLayoutConfig.fontFamily }">
                <div v-if="previewIsWangSheng && previewDisplayItems.includes('yangshang')" class="preview-yangshang-area" :style="getYangshangAreaStyle(previewLayoutConfig)">
                  <span class="capacity-badge" :style="{ background: '#67c23a' }">横 {{ charCapacityOf(previewLayoutConfig, 'yangshang').horz }} × 竖 {{ charCapacityOf(previewLayoutConfig, 'yangshang').vert }} 字{{ previewLayoutConfig.yangshangRows === 2 ? ' / 行' : '' }}</span>
                <div v-for="(pair, pIdx) in yangshangPairs(alignedPreviewYangshangNames, previewLayoutConfig.yangshangRows)" :key="'ysp-'+pIdx" class="ys-pair" :style="ysPairStyle(previewLayoutConfig)">
                  <div v-for="item in pair" :key="'ys-'+item.idx" :style="(previewLayoutConfig.yangshangRows === 1 && previewLayoutConfig.yangshangAutoAdjust && previewLayoutConfig.yangshangVertAlign !== 'center') ? getYangshangFillItemStyle(previewLayoutConfig) : getYangshangItemStyle(previewLayoutConfig, item.idx)">
                    <template v-if="previewLayoutConfig.yangshangRows === 1 && previewLayoutConfig.yangshangAutoAdjust && previewLayoutConfig.yangshangVertAlign !== 'center'"><span v-for="(ch, ci) in item.name" :key="ci" :style="{ fontSize: previewLayoutConfig.yangshangFontSize + 'px', lineHeight: '1' }">{{ ch }}</span></template>
                    <template v-else>{{ item.name }}</template>
                  </div>
                </div>
              </div>
                <div class="preview-names-area" :style="getNamesAreaStyle(previewLayoutConfig)">
                  <span class="capacity-badge" :style="{ background: '#f56c6c' }">横 {{ charCapacityOf(previewLayoutConfig, 'name').horz }} × 竖 {{ charCapacityOf(previewLayoutConfig, 'name').vert }} 字</span>
                  <div v-for="(name, idx) in alignedPreviewNames" :key="'n-'+idx" :style="(previewLayoutConfig.nameAutoAdjust && previewLayoutConfig.nameVertAlign !== 'center') ? getNameFillItemStyle(previewLayoutConfig) : getNameItemStyle(previewLayoutConfig)">
                    <template v-if="previewLayoutConfig.nameAutoAdjust && previewLayoutConfig.nameVertAlign !== 'center'"><span v-for="(ch, ci) in name" :key="ci" :style="{ fontSize: previewLayoutConfig.nameFontSize + 'px', lineHeight: '1' }">{{ ch }}</span></template>
                    <template v-else>{{ name }}</template>
                  </div>
                </div>
                <div v-if="previewDisplayItems.includes('seat') || previewDisplayItems.includes('fahui_name') || previewDisplayItems.includes('shizhu_name')" class="preview-bottom" :style="getBottomAreaStyle(previewLayoutConfig)">
                  <span v-if="previewDisplayItems.includes('shizhu_name')">{{ sampleData.shizhu_name }} </span>
                  <span v-if="previewDisplayItems.includes('fahui_name')">{{ sampleData.fahui_name }} </span>
                  <span v-if="previewDisplayItems.includes('seat')">{{ sampleData.seat }}</span>
                </div>
              </div>
            </div>
            <svg v-if="previewDialogShowRuler" class="ruler-overlay" :width="previewPageStyleForDialog.width" :height="previewPageStyleForDialog.height" xmlns="http://www.w3.org/2000/svg">
              <line v-for="t in dialogRulerTicks.filter(t => t.type === 'h')" :key="'h'+t.mm" :x1="t.x" y1="0" :x2="t.x" :y2="t.major ? 20 : 10" stroke="red" stroke-width="0.5" />
              <text v-for="t in dialogRulerTicks.filter(t => t.type === 'h' && t.mm % 50 === 0)" :key="'ht'+t.mm" :x="t.x" y="30" font-size="10" fill="red" text-anchor="middle">{{ t.mm }}mm</text>
              <line v-for="t in dialogRulerTicks.filter(t => t.type === 'v')" :key="'v'+t.mm" x1="0" :y1="t.y" :x2="t.major ? 20 : 10" :y2="t.y" stroke="red" stroke-width="0.5" />
              <text v-for="t in dialogRulerTicks.filter(t => t.type === 'v' && t.mm % 50 === 0)" :key="'vt'+t.mm" x="30" :y="t.y + 4" font-size="10" fill="red" text-anchor="middle">{{ t.mm }}mm</text>
              <line v-for="gl in dialogGuideLines" :key="gl.key" :x1="gl.x1" :y1="gl.y1" :x2="gl.x2" :y2="gl.y2" stroke="rgba(0,120,255,0.5)" stroke-width="0.8" stroke-dasharray="6,4" />
            </svg>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { printerTemplateApi } from '@/api/printerTemplates'
import TemplateEditor from '@/components/TemplateEditor.vue'

const loading = ref(false)
const tableData = ref([])
const previewVisible = ref(false)

const editorVisible = ref(false)
const editingTemplate = ref(null)
const editorCopyMode = ref(false)

const handleAdd = () => {
  editingTemplate.value = null
  editorCopyMode.value = false
  editorVisible.value = true
}

const handleEdit = (row) => {
  editingTemplate.value = row
  editorCopyMode.value = false
  editorVisible.value = true
}

const handleCopy = (row) => {
  editingTemplate.value = row
  editorCopyMode.value = true
  editorVisible.value = true
}

const onEditorSaved = () => {
  fetchData()
}

const defaultLayoutConfig = {
  pageWidth: 210,
  pageHeight: 297,
  smallPaperOnA4: false,
  smallPaperAlign: 'center',
  smallPaperVAlign: 'top',
  flipH: false,
  flipV: false,
  fontFamily: 'STXingkai',
  nameFontSize: 52,
  nameSpacing: 20,
  nameCharSpacing: 1.3,
  nameVertAlign: 'top',
  nameAutoAdjust: false,
  autoPadNames: true,
  namesTopPct: 25,
  namesLeftPct: 10,
  namesWidthPct: 80,
  namesHeightPct: 55,
  yangshangFontSize: 18,
  yangshangSpacing: 5,
  yangshangCharSpacing: 1.3,
  yangshangVertAlign: 'top',
  yangshangAutoAdjust: false,
  autoPadYangshang: true,
  yangshangTopPct: 25,
  yangshangLeftPct: 2,
  yangshangWidthPct: 20,
  yangshangHeightPct: 55,
  yangshangRows: 1,
  seatFontSize: 24,
  bottomTopPct: 90,
  bottomLeftPct: 50,
  backgroundImage: '',
  backgroundOpacity: 30,
  printBackground: false,
  printRuler: false,
  printOffsetY: 0
}

const sampleData = reactive({
  fahui_name: '示例法会',
  seat: '0001',
  shizhu_name: '张施主',
  names_yansheng: ['张三', '李四', '王五'],
  names_wangsheng_jieyin: ['赵六', '钱七', '孙八', '李九'],
  names_wangsheng_yangshang: ['周一', '吴二', '郑三']
})

const previewFormData = reactive({
  id: null,
  模板名称: '',
  模板类型: '',
  牌位类型: '',
  是否启用: 1,
  备注: ''
})

const previewLayoutConfig = reactive({ ...defaultLayoutConfig })
const previewDisplayItems = ref(['seat', 'fahui_name'])
const previewIsWangSheng = computed(() => previewFormData.模板类型 === '往生牌位')

const previewNames = computed(() => {
  if (previewIsWangSheng.value) return sampleData.names_wangsheng_jieyin
  return sampleData.names_yansheng
})

const previewYangshangNames = computed(() => {
  if (!previewIsWangSheng.value) return []
  return sampleData.names_wangsheng_yangshang
})

const previewDialogShowRuler = ref(false)

const splitNameSuffix = (name) => {
  if (!name) return { namePart: '', suffix: '' }
  const trimmed = name.trim()
  const lastSpaceIdx = trimmed.lastIndexOf(' ')
  if (lastSpaceIdx >= 0) {
    return {
      namePart: trimmed.substring(0, lastSpaceIdx).replace(/ /g, ''),
      suffix: trimmed.substring(lastSpaceIdx + 1)
    }
  }
  return { namePart: trimmed.replace(/ /g, ''), suffix: '' }
}

const padNamePart = (namePart, maxLen) => {
  if (namePart.length >= maxLen) return namePart
  const padding = maxLen - namePart.length
  const gaps = namePart.length - 1
  if (gaps <= 0) return namePart + '\u3000'.repeat(padding)
  const base = Math.floor(padding / gaps)
  const extra = padding % gaps
  let result = ''
  for (let i = 0; i < namePart.length; i++) {
    result += namePart[i]
    if (i < gaps) {
      const spaces = base + (i < extra ? 1 : 0)
      result += '\u3000'.repeat(spaces)
    }
  }
  return result
}

const normalizeRawName = (name) => {
  if (!name) return ''
  return name.split(/\s+/).filter(Boolean).join('\u3000')
}

const parsedPreviewNames = computed(() => previewNames.value.map(n => splitNameSuffix(n)))
const maxPreviewNamePartLen = computed(() => Math.max(...parsedPreviewNames.value.map(n => n.namePart.length), 0))

const alignedPreviewNames = computed(() => {
  if (previewLayoutConfig.autoPadNames === false) {
    return previewNames.value.map(normalizeRawName)
  }
  return parsedPreviewNames.value.map(parsed => {
    const padded = padNamePart(parsed.namePart, maxPreviewNamePartLen.value)
    return padded + (parsed.suffix ? parsed.suffix : '')
  })
})

const parsedPreviewYangshangNames = computed(() => previewYangshangNames.value.map(n => splitNameSuffix(n)))
const maxPreviewYangshangNamePartLen = computed(() => Math.max(...parsedPreviewYangshangNames.value.map(n => n.namePart.length), 0))

const alignedPreviewYangshangNames = computed(() => {
  if (previewLayoutConfig.autoPadYangshang === false) {
    return previewYangshangNames.value.map(normalizeRawName)
  }
  return parsedPreviewYangshangNames.value.map(parsed => {
    const padded = padNamePart(parsed.namePart, maxPreviewYangshangNamePartLen.value)
    return padded + (parsed.suffix ? parsed.suffix : '')
  })
})

const PX_TO_MM = 0.2645833
const charCapacityOf = (cfg, kind) => {
  if (!cfg) return { vert: 0, horz: 0 }
  const pageW = cfg.pageWidth || 210
  const pageH = cfg.pageHeight || 297
  if (kind === 'yangshang') {
    const areaW = pageW * (cfg.yangshangWidthPct ?? 20) / 100
    const areaH = pageH * (cfg.yangshangHeightPct ?? 55) / 100
    const rows = cfg.yangshangRows === 2 ? 2 : 1
    const fs = cfg.yangshangFontSize || 18
    const vPitch = fs * PX_TO_MM * (cfg.yangshangCharSpacing || 1.3)
    const hStep = (fs * 1.2 + (cfg.yangshangSpacing || 5)) * PX_TO_MM
    const vert = vPitch > 0 ? Math.max(0, Math.floor((areaH / rows) / vPitch)) : 0
    const horz = hStep > 0 ? Math.max(0, Math.floor(areaW / hStep)) : 0
    return { vert, horz }
  }
  const areaW = pageW * (cfg.namesWidthPct ?? 80) / 100
  const areaH = pageH * (cfg.namesHeightPct ?? 55) / 100
  const fs = cfg.nameFontSize || 52
  const vPitch = fs * PX_TO_MM * (cfg.nameCharSpacing || 1.3)
  const hStep = (fs + (cfg.nameSpacing || 20)) * PX_TO_MM
  const vert = vPitch > 0 ? Math.max(0, Math.floor(areaH / vPitch)) : 0
  const horz = hStep > 0 ? Math.max(0, Math.floor(areaW / hStep)) : 0
  return { vert, horz }
}

const getNamesAreaStyle = (cfg) => {
  const offsetY = cfg.printOffsetY || 0
  const pageH = cfg.pageHeight || 297
  const offsetPct = -(offsetY / pageH * 100)
  return {
    position: 'absolute',
    top: cfg.namesTopPct + offsetPct + '%',
    left: cfg.namesLeftPct + '%',
    width: cfg.namesWidthPct + '%',
    height: cfg.namesHeightPct + '%',
    display: 'flex',
    flexDirection: 'row-reverse',
    justifyContent: 'center',
    alignItems: (cfg.nameAutoAdjust && cfg.nameVertAlign === 'center') ? 'center' : 'flex-start',
    boxSizing: 'border-box',
    border: '1px dashed #f56c6c'
  }
}

const getYangshangAreaStyle = (cfg) => {
  const offsetY = cfg.printOffsetY || 0
  const pageH = cfg.pageHeight || 297
  const offsetPct = -(offsetY / pageH * 100)
  return {
    position: 'absolute',
    top: (cfg.yangshangTopPct ?? 25) + offsetPct + '%',
    left: (cfg.yangshangLeftPct ?? 2) + '%',
    width: (cfg.yangshangWidthPct ?? 20) + '%',
    height: (cfg.yangshangHeightPct ?? 55) + '%',
    display: 'flex',
    flexDirection: 'row-reverse',
    alignItems: (cfg.yangshangAutoAdjust && cfg.yangshangRows === 1 && cfg.yangshangVertAlign === 'center') ? 'center' : 'flex-start',
    boxSizing: 'border-box',
    border: '1px dashed #67c23a'
  }
}

const getNameItemStyle = (cfg) => ({
  writingMode: 'vertical-rl',
  fontSize: cfg.nameFontSize + 'px',
  lineHeight: '1.2',
  letterSpacing: ((cfg.nameCharSpacing || 1.3) - 1.0) + 'em',
  margin: '0 ' + cfg.nameSpacing / 2 + 'px',
  whiteSpace: 'nowrap'
})

const getNameFillItemStyle = (cfg) => ({
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  height: '100%',
  alignItems: 'center',
  fontSize: cfg.nameFontSize + 'px',
  lineHeight: '1',
  margin: '0 ' + cfg.nameSpacing / 2 + 'px',
  whiteSpace: 'nowrap'
})

const getBottomAreaStyle = (cfg) => {
  const offsetY = cfg.printOffsetY || 0
  const pageH = cfg.pageHeight || 297
  const offsetPct = -(offsetY / pageH * 100)
  return {
    position: 'absolute',
    top: (cfg.bottomTopPct ?? 90) + offsetPct + '%',
    left: (cfg.bottomLeftPct ?? 50) + '%',
    transform: 'translateX(-50%)',
    fontSize: (cfg.seatFontSize || 24) + 'px',
    textAlign: 'center',
    zIndex: 1
  }
}

const yangshangPairs = (names, rows) => {
  const arr = names || []
  if ((rows || 1) === 1) {
    return arr.map((name, i) => [{ name, idx: i }])
  }
  const pairs = []
  for (let i = 0; i < arr.length; i += 2) {
    const pair = []
    if (arr[i] !== undefined) pair.push({ name: arr[i], idx: i })
    if (arr[i + 1] !== undefined) pair.push({ name: arr[i + 1], idx: i + 1 })
    pairs.push(pair)
  }
  return pairs
}

const ysPairStyle = (cfg) => ({
  display: 'flex',
  flexDirection: 'column',
  justifyContent: ((cfg.yangshangRows || 1) === 2) ? 'space-between' : 'flex-start',
  height: '100%',
  alignItems: 'center',
  margin: '0 ' + ((cfg.yangshangSpacing || 5) / 2) + 'px',
  boxSizing: 'border-box'
})

const getYangshangItemStyle = (cfg, idx) => ({
  writingMode: 'vertical-rl',
  fontSize: (cfg.yangshangFontSize || 18) + 'px',
  lineHeight: '1.2',
  letterSpacing: ((cfg.yangshangCharSpacing || 1.3) - 1.0) + 'em',
  margin: '0',
  whiteSpace: 'nowrap'
})

const getYangshangFillItemStyle = (cfg) => ({
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  height: '100%',
  alignItems: 'center',
  fontSize: (cfg.yangshangFontSize || 18) + 'px',
  lineHeight: '1',
  margin: '0',
  whiteSpace: 'nowrap'
})

const CAL_KEY_X = 'print_cal_scale_x'
const CAL_KEY_Y = 'print_cal_scale_y'
const calScaleX = ref(parseFloat(localStorage.getItem(CAL_KEY_X)) || 1.0)
const calScaleY = ref(parseFloat(localStorage.getItem(CAL_KEY_Y)) || 1.0)

const BASE_PX_PER_MM = 96 / 25.4
const A4_W_MM = 210
const A4_H_MM = 297

const computeSmallPaperOffset = (layout) => {
  const lwMm = layout.pageWidth || 210
  const lhMm = layout.pageHeight || 297
  const align = layout.smallPaperAlign || 'center'
  let offsetXmm
  if (align === 'left') offsetXmm = 0
  else if (align === 'right') offsetXmm = A4_W_MM - lwMm
  else offsetXmm = (A4_W_MM - lwMm) / 2
  const vAlign = layout.smallPaperVAlign || 'top'
  const offsetYmm = vAlign === 'bottom' ? (A4_H_MM - lhMm) : 0
  return { offsetXmm, offsetYmm }
}

const dialogRulerTicks = computed(() => {
  const pmm = BASE_PX_PER_MM
  const wMm = previewLayoutConfig.smallPaperOnA4 ? A4_W_MM : (previewLayoutConfig.pageWidth || 210)
  const hMm = previewLayoutConfig.smallPaperOnA4 ? A4_H_MM : (previewLayoutConfig.pageHeight || 297)
  const ticks = []
  for (let mm = 0; mm <= wMm; mm += 10) {
    ticks.push({ type: 'h', mm, x: mm * pmm, major: mm % 50 === 0 })
  }
  for (let mm = 0; mm <= hMm; mm += 10) {
    ticks.push({ type: 'v', mm, y: mm * pmm, major: mm % 50 === 0 })
  }
  return ticks
})

const dialogGuideLines = computed(() => {
  const pmm = BASE_PX_PER_MM
  const wMm = previewLayoutConfig.smallPaperOnA4 ? A4_W_MM : (previewLayoutConfig.pageWidth || 210)
  const hMm = previewLayoutConfig.smallPaperOnA4 ? A4_H_MM : (previewLayoutConfig.pageHeight || 297)
  const w = wMm * pmm
  const h = hMm * pmm
  const lines = []
  for (let cm = 1; cm < wMm / 10; cm++) {
    const x = cm * 10 * pmm
    lines.push({ key: 'v' + cm, x1: x, y1: 0, x2: x, y2: h })
  }
  for (let cm = 1; cm < hMm / 10; cm++) {
    const y = cm * 10 * pmm
    lines.push({ key: 'h' + cm, x1: 0, y1: y, x2: w, y2: y })
  }
  return lines
})

const previewPageStyleForDialog = computed(() => {
  const wMm = previewLayoutConfig.smallPaperOnA4 ? A4_W_MM : (previewLayoutConfig.pageWidth || 210)
  const hMm = previewLayoutConfig.smallPaperOnA4 ? A4_H_MM : (previewLayoutConfig.pageHeight || 297)
  const w = wMm * BASE_PX_PER_MM
  const h = hMm * BASE_PX_PER_MM
  const fx = previewLayoutConfig.flipH ? -1 : 1
  const fy = previewLayoutConfig.flipV ? -1 : 1
  const tx = previewLayoutConfig.flipH ? w : 0
  const ty = previewLayoutConfig.flipV ? h : 0
  return {
    width: w + 'px',
    height: h + 'px',
    transform: `translate(${tx}px, ${ty}px) scale(${calScaleX.value * fx}, ${calScaleY.value * fy})`,
    transformOrigin: 'top left'
  }
})

const previewWrapperStyleForDialog = computed(() => {
  const wMm = previewLayoutConfig.smallPaperOnA4 ? A4_W_MM : (previewLayoutConfig.pageWidth || 210)
  const hMm = previewLayoutConfig.smallPaperOnA4 ? A4_H_MM : (previewLayoutConfig.pageHeight || 297)
  const w = wMm * BASE_PX_PER_MM * calScaleX.value
  const h = hMm * BASE_PX_PER_MM * calScaleY.value
  return { width: w + 'px', height: h + 'px' }
})

const previewScalerStyleForDialog = computed(() => {
  const lwMm = previewLayoutConfig.pageWidth || 210
  const lhMm = previewLayoutConfig.pageHeight || 297
  if (!previewLayoutConfig.smallPaperOnA4) {
    return { width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }
  }
  const { offsetXmm, offsetYmm } = computeSmallPaperOffset(previewLayoutConfig)
  return {
    width: (lwMm * BASE_PX_PER_MM) + 'px',
    height: (lhMm * BASE_PX_PER_MM) + 'px',
    position: 'absolute',
    top: '0',
    left: '0',
    transform: `translate(${offsetXmm * BASE_PX_PER_MM}px, ${offsetYmm * BASE_PX_PER_MM}px)`,
    transformOrigin: 'top left'
  }
})

const dialogSmallPaperIndicatorStyle = computed(() => {
  if (!previewLayoutConfig.smallPaperOnA4) return { display: 'none' }
  const lwMm = previewLayoutConfig.pageWidth || 210
  const lhMm = previewLayoutConfig.pageHeight || 297
  const { offsetXmm, offsetYmm } = computeSmallPaperOffset(previewLayoutConfig)
  return {
    position: 'absolute',
    top: (offsetYmm * BASE_PX_PER_MM) + 'px',
    left: (offsetXmm * BASE_PX_PER_MM) + 'px',
    width: (lwMm * BASE_PX_PER_MM) + 'px',
    height: (lhMm * BASE_PX_PER_MM) + 'px',
    border: '2px dashed #67c23a',
    pointerEvents: 'none',
    zIndex: 5
  }
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await printerTemplateApi.getList()
    tableData.value = res
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const migrateOldConfig = (config) => {
  if (config.nameFontSize === undefined && config.nameFontSize1 !== undefined) {
    config.nameFontSize = config.nameFontSize3 || 44
    config.nameSpacing = 20
    config.namesTopPct = 25
    config.namesLeftPct = 10
    config.namesWidthPct = 80
    config.namesHeightPct = 55
    config.yangshangSpacing = config.yangshangSpacing || 5
    delete config.nameFontSize1
    delete config.nameFontSize2
    delete config.nameFontSize3
    delete config.nameFontSize4
    delete config.nameFontSize5
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该模板吗？', '提示', { type: 'warning' })
    await printerTemplateApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

const handleSetDefault = async (row) => {
  try {
    await printerTemplateApi.setDefault(row.id)
    ElMessage.success('已设为默认模板')
    fetchData()
  } catch (error) {
    console.error('设置默认失败:', error)
    ElMessage.error('设置默认失败')
  }
}

const handlePreviewFromList = (row) => {
  Object.assign(previewFormData, {
    id: row.id,
    模板名称: row.模板名称,
    模板类型: row.模板类型,
    牌位类型: row.牌位类型,
    是否启用: row.是否启用,
    备注: row.备注
  })
  Object.assign(previewLayoutConfig, { ...defaultLayoutConfig })
  if (row.布局配置) {
    try {
      const config = JSON.parse(row.布局配置)
      if (config.layout) {
        const migrated = { ...defaultLayoutConfig, ...config.layout }
        migrateOldConfig(migrated)
        Object.assign(previewLayoutConfig, migrated)
      }
      if (config.displayItems) previewDisplayItems.value = config.displayItems
    } catch (e) {
      console.error('解析布局配置失败:', e)
    }
  }
  previewVisible.value = true
}

const openPdfFromConfig = async (config, names, yangshangNames, seat, fahuiName, shizhuName) => {
  try {
    const isWs = config._template_type === '往生牌位'
    const records = [{
      xm1: names[0] || '',
      xm2: names[1] || '',
      xm3: names[2] || '',
      xm4: names[3] || '',
      xm5: isWs ? (yangshangNames[0] || '') : (names[4] || ''),
      xm6: yangshangNames[1] || '',
      xm7: yangshangNames[2] || '',
      xm8: yangshangNames[3] || '',
      xm9: yangshangNames[4] || '',
      xm10: yangshangNames[5] || '',
      fahui_name: fahuiName,
      zuoweinum: seat,
      shizhu_name: shizhuName
    }]
    const response = await printerTemplateApi.generatePdfFromConfig({
      config: config,
      records: records,
      filename: config._templateName || 'preview'
    })
    const blob = new Blob([response], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  } catch (error) {
    console.error('PDF生成失败:', error)
    ElMessage.error('PDF生成失败')
  }
}

const handlePrintPreviewFromDialog = () => {
  const names = previewIsWangSheng.value ? sampleData.names_wangsheng_jieyin : sampleData.names_yansheng
  const yangshangNames = previewIsWangSheng.value ? sampleData.names_wangsheng_yangshang : []
  const config = {
    layout: { ...previewLayoutConfig },
    displayItems: previewDisplayItems.value,
    _template_type: previewFormData.模板类型 || (previewIsWangSheng.value ? '往生牌位' : '延生牌位'),
    _templateName: previewFormData.模板名称
  }
  openPdfFromConfig(config, names, yangshangNames, sampleData.seat, sampleData.fahui_name, sampleData.shizhu_name)
}

onMounted(() => { fetchData() })
</script>

<style scoped>
.template-list { height: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.preview-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 6px 10px; background: #f5f7fa; border-radius: 4px; gap: 8px; }
.zoom-control { display: flex; align-items: center; gap: 6px; flex: 1; justify-content: center; }
.zoom-value { font-size: 12px; color: #409eff; min-width: 36px; text-align: center; }
.preview-info { color: #606266; font-size: 13px; }
.preview-container { background: #e8e8e8; border-radius: 4px; padding: 15px; overflow: auto; }
.preview-page-wrapper { margin: 0 auto; pointer-events: none; }
.preview-page { background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.15); box-sizing: border-box; position: relative; overflow: hidden; pointer-events: auto; }
.ruler-overlay { position: absolute; top: 0; left: 0; pointer-events: none; z-index: 10; }
.preview-bg-image { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; pointer-events: none; }
.preview-content { width: 100%; height: 100%; position: relative; z-index: 1; }
.preview-yangshang-area { display: flex; flex-direction: row-reverse; align-items: flex-start; }
.preview-names-area { display: flex; flex-direction: row-reverse; justify-content: center; align-items: flex-start; }
.preview-bottom { position: absolute; z-index: 1; }
.preview-bottom span { display: block; }
.capacity-badge { position: absolute; top: -20px; left: 0; z-index: 10; padding: 1px 6px; font-size: 12px; font-weight: 600; line-height: 1.5; color: #fff; border-radius: 3px; white-space: nowrap; pointer-events: none; font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; }
</style>
