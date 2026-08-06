<template>
  <el-dialog v-model="dialogVisible" title="打印预览" width="800px" destroy-on-close @close="handleClose">
    <div class="preview-toolbar">
      <div>
        <span style="margin-right: 10px;">打印模板:</span>
        <el-select v-model="selectedTemplateId" placeholder="选择打印模板" style="width: 250px">
          <el-option v-for="item in templateList" :key="item.id" :label="item.模板名称" :value="item.id" />
        </el-select>
      </div>
      <div class="zoom-control">
        <el-button size="small" @click="showRuler = !showRuler" :type="showRuler ? 'warning' : ''">标尺</el-button>
        <el-button size="small" @click="showCalibrate = !showCalibrate" :type="showCalibrate ? 'warning' : ''">校准</el-button>
        <span class="zoom-value" style="margin-left: 4px">X:{{ (calScaleX * 100).toFixed(0) }}% Y:{{ (calScaleY * 100).toFixed(0) }}%</span>
      </div>
    </div>
    <div v-if="showCalibrate" class="calibrate-panel">
      <div class="calibrate-row">
        <span class="cal-label">横向校准：</span>
        <span>红条标称 {{ calTargetMmX }}mm，用尺子量实际</span>
        <el-input-number v-model="calMeasuredMmX" :min="1" :max="500" :precision="1" size="small" style="width: 100px" />
        <span>mm</span>
        <el-button size="small" type="primary" @click="applyCalibrationX">应用</el-button>
        <el-button size="small" @click="calScaleX = 1.0; saveCalibration()">重置</el-button>
        <div :style="calBarStyleX"></div>
      </div>
      <div class="calibrate-row">
        <span class="cal-label">纵向校准：</span>
        <span>红条标称 {{ calTargetMmY }}mm，用尺子量实际</span>
        <el-input-number v-model="calMeasuredMmY" :min="1" :max="500" :precision="1" size="small" style="width: 100px" />
        <span>mm</span>
        <el-button size="small" type="primary" @click="applyCalibrationY">应用</el-button>
        <el-button size="small" @click="calScaleY = 1.0; saveCalibration()">重置</el-button>
        <div :style="calBarStyleY" style="display: inline-block; vertical-align: middle"></div>
      </div>
    </div>
    <div class="preview-container">
      <div class="preview-page-wrapper" :style="previewWrapperStyle">
        <div class="preview-page" :style="previewPageStyle">
          <div class="small-paper-indicator" :style="smallPaperIndicatorStyle"></div>
          <div class="preview-scaler" :style="previewScalerStyle">
            <img v-if="resolvedLayout.backgroundImage" :src="resolvedLayout.backgroundImage" class="preview-bg-image" :style="{ opacity: (resolvedLayout.backgroundOpacity || 30) / 100 }" />
            <div class="preview-content" :style="previewContentStyle">
              <div v-if="isWangSheng && resolvedDisplayItems.includes('yangshang')" class="preview-yangshang-area" :style="yangshangAreaStyle">
              <div v-for="(name, idx) in alignedYangshangNames" :key="'ys-'+idx" :style="yangshangItemStyle">{{ name }}</div>
            </div>
              <div class="preview-names-area" :style="namesAreaStyle">
                <div v-for="(name, idx) in alignedMainNames" :key="'n-'+idx" :style="nameItemStyle">{{ name }}</div>
              </div>
              <div v-if="resolvedDisplayItems.includes('seat') || resolvedDisplayItems.includes('fahui_name') || resolvedDisplayItems.includes('shizhu_name')" class="preview-bottom" :style="bottomAreaStyle">
                <span v-if="resolvedDisplayItems.includes('shizhu_name')">{{ record.施主姓名 }} </span>
                <span v-if="resolvedDisplayItems.includes('fahui_name')">{{ record.fahui_name }} </span>
                <span v-if="resolvedDisplayItems.includes('seat')">{{ record.zuoweinum || record.座次 || '' }}</span>
              </div>
            </div>
          </div>
          <svg v-if="showRuler" class="ruler-overlay" :width="previewPageStyle.width" :height="previewPageStyle.height" xmlns="http://www.w3.org/2000/svg">
            <line v-for="t in rulerTicks.filter(t => t.type === 'h')" :key="'h'+t.mm" :x1="t.x" y1="0" :x2="t.x" :y2="t.major ? 20 : 10" stroke="red" stroke-width="0.5" />
            <text v-for="t in rulerTicks.filter(t => t.type === 'h' && t.mm % 50 === 0)" :key="'ht'+t.mm" :x="t.x" y="30" font-size="10" fill="red" text-anchor="middle">{{ t.mm }}mm</text>
            <line v-for="t in rulerTicks.filter(t => t.type === 'v')" :key="'v'+t.mm" x1="0" :y1="t.y" :x2="t.major ? 20 : 10" :y2="t.y" stroke="red" stroke-width="0.5" />
            <text v-for="t in rulerTicks.filter(t => t.type === 'v' && t.mm % 50 === 0)" :key="'vt'+t.mm" x="30" :y="t.y + 4" font-size="10" fill="red" text-anchor="middle">{{ t.mm }}mm</text>
            <line v-for="gl in guideLines" :key="gl.key" :x1="gl.x1" :y1="gl.y1" :x2="gl.x2" :y2="gl.y2" stroke="rgba(0,120,255,0.5)" stroke-width="0.8" stroke-dasharray="6,4" />
          </svg>
        </div>
      </div>
    </div>
    <template #footer>
      <slot name="footer-extra"></slot>
      <el-button @click="dialogVisible = false">关闭</el-button>
      <el-button type="primary" @click="doPrint" :disabled="!selectedTemplateId">打印</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { printerTemplateApi } from '@/api/printerTemplates'
import { fahuiRecordApi } from '@/api/fahuiRecords'

const props = defineProps({
  visible: Boolean,
  record: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:visible', 'printed'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const handleClose = () => {
  emit('update:visible', false)
}

const templateList = ref([])
const selectedTemplateId = ref(null)
const A4_W_MM = 210
const A4_H_MM = 297

// 小纸A4对齐模式：打印机驱动设A4走纸，实际送小纸，内容不缩放偏移到小纸位置
const smallPaperOnA4 = computed(() => resolvedLayout.value.smallPaperOnA4 === true)
// 预览画布是否用A4尺寸（小纸A4模式用A4画布）
const useA4Canvas = computed(() => smallPaperOnA4.value)

const isWangSheng = computed(() => props.record.yanwang === 1)

const fetchTemplateList = async () => {
  try {
    const templateType = isWangSheng.value ? '往生牌位' : '延生牌位'
    const res = await printerTemplateApi.getList(templateType)
    templateList.value = res.filter(t => t.是否启用 === 1)
    if (templateList.value.length > 0) {
      const defaultTemplate = templateList.value.find(t => t.是否默认 === 1)
      selectedTemplateId.value = defaultTemplate ? defaultTemplate.id : templateList.value[0].id
    }
  } catch (error) {
    console.error('获取模板列表失败:', error)
  }
}

watch(() => props.visible, (val) => {
  if (val) {
    selectedTemplateId.value = null
    fetchTemplateList()
  }
})

const defaultLayout = {
  pageWidth: 210, pageHeight: 297,
  printerMargin: 5,
  fontFamily: 'STXingkai',
  nameFontSize: 52, nameSpacing: 20,
  autoPadNames: true,
  namesTopPct: 25, namesLeftPct: 10,
  namesWidthPct: 80, namesHeightPct: 55,
  yangshangFontSize: 18, yangshangSpacing: 5,
  yangshangCharSpacing: 1.3,
  autoPadYangshang: true,
  yangshangTopPct: 25, yangshangLeftPct: 2,
  yangshangWidthPct: 20, yangshangHeightPct: 55,
  seatFontSize: 24
}

const currentTemplate = computed(() => {
  return templateList.value.find(t => t.id === selectedTemplateId.value)
})

const templateConfig = computed(() => {
  const template = currentTemplate.value
  if (!template || !template.布局配置) {
    return {
      layout: { ...defaultLayout },
      content: { namesTitle: isWangSheng.value ? '佛光接引' : '佛光注照' },
      displayItems: ['seat', 'fahui_name']
    }
  }
  try {
    const config = JSON.parse(template.布局配置)
    return config
  } catch (e) {
    return {
      layout: { ...defaultLayout },
      content: { namesTitle: isWangSheng.value ? '佛光接引' : '佛光注照' },
      displayItems: ['seat', 'fahui_name']
    }
  }
})

const resolvedLayout = computed(() => ({ ...defaultLayout, ...templateConfig.value.layout }))
const resolvedDisplayItems = computed(() => {
  const items = templateConfig.value.displayItems || ['seat', 'fahui_name']
  // 往生牌位默认启用阳上显示（兼容旧模板）
  if (isWangSheng.value && !items.includes('yangshang')) {
    return [...items, 'yangshang']
  }
  return items
})

const mainNames = computed(() => {
  const row = props.record
  if (isWangSheng.value) {
    return [row.xm1, row.xm2, row.xm3, row.xm4].filter(Boolean)
  }
  return [row.xm1, row.xm2, row.xm3, row.xm4, row.xm5].filter(Boolean)
})

const yangshangNames = computed(() => {
  if (!isWangSheng.value) return []
  const row = props.record
  return [row.xm5, row.xm6, row.xm7, row.xm8, row.xm9, row.xm10].filter(Boolean)
})

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

const parsedMainNames = computed(() => {
  return mainNames.value.map(n => splitNameSuffix(n))
})

const maxNamePartLen = computed(() => {
  return Math.max(...parsedMainNames.value.map(n => n.namePart.length), 0)
})

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

const alignedMainNames = computed(() => {
  if (resolvedLayout.value.autoPadNames === false) {
    return mainNames.value
  }
  return parsedMainNames.value.map(parsed => {
    const padded = padNamePart(parsed.namePart, maxNamePartLen.value)
    return padded + (parsed.suffix ? parsed.suffix : '')
  })
})

const parsedYangshangNames = computed(() => {
  return yangshangNames.value.map(n => splitNameSuffix(n))
})

const maxYangshangNamePartLen = computed(() => {
  return Math.max(...parsedYangshangNames.value.map(n => n.namePart.length), 0)
})

const alignedYangshangNames = computed(() => {
  if (resolvedLayout.value.autoPadYangshang === false) {
    return yangshangNames.value
  }
  return parsedYangshangNames.value.map(parsed => {
    const padded = padNamePart(parsed.namePart, maxYangshangNamePartLen.value)
    return padded + (parsed.suffix ? parsed.suffix : '')
  })
})

const namesAreaStyle = computed(() => {
  const l = resolvedLayout.value
  const offsetY = l.printOffsetY || 0
  const pageH = l.pageHeight || 297
  const offsetPct = -(offsetY / pageH * 100)
  return {
    position: 'absolute',
    top: (l.namesTopPct ?? 25) + offsetPct + '%',
    left: (l.namesLeftPct ?? 10) + '%',
    width: (l.namesWidthPct ?? 80) + '%',
    height: (l.namesHeightPct ?? 55) + '%',
    display: 'flex',
    flexDirection: 'row-reverse',
    justifyContent: 'center',
    alignItems: 'flex-start',
    boxSizing: 'border-box'
  }
})

const yangshangAreaStyle = computed(() => {
  const l = resolvedLayout.value
  const offsetY = l.printOffsetY || 0
  const pageH = l.pageHeight || 297
  const offsetPct = -(offsetY / pageH * 100)
  return {
    position: 'absolute',
    top: (l.yangshangTopPct ?? 25) + offsetPct + '%',
    left: (l.yangshangLeftPct ?? 2) + '%',
    width: (l.yangshangWidthPct ?? 20) + '%',
    height: (l.yangshangHeightPct ?? 55) + '%',
    display: 'flex',
    flexDirection: 'row-reverse',
    alignItems: 'flex-start',
    boxSizing: 'border-box'
  }
})

const previewContentStyle = computed(() => {
  const l = resolvedLayout.value
  return {
    fontFamily: l.fontFamily || 'STXingkai'
  }
})

const nameItemStyle = computed(() => {
  const l = resolvedLayout.value
  return {
    writingMode: 'vertical-rl',
    fontSize: (l.nameFontSize || 52) + 'px',
    lineHeight: '1.2',
    letterSpacing: ((l.nameCharSpacing || 1.3) - 1.0) + 'em',
    margin: '0 ' + ((l.nameSpacing || 20) / 2) + 'px'
  }
})

const yangshangItemStyle = computed(() => {
  const l = resolvedLayout.value
  return {
    writingMode: 'vertical-rl',
    fontSize: (l.yangshangFontSize || 18) + 'px',
    lineHeight: '1.2',
    letterSpacing: ((l.yangshangCharSpacing || 1.3) - 1.0) + 'em',
    margin: '0 ' + ((l.yangshangSpacing || 5) / 2) + 'px'
  }
})

const bottomAreaStyle = computed(() => {
  const l = resolvedLayout.value
  const offsetY = l.printOffsetY || 0
  const pageH = l.pageHeight || 297
  const offsetPct = -(offsetY / pageH * 100)
  return {
    position: 'absolute',
    top: (l.bottomTopPct ?? 90) + offsetPct + '%',
    left: (l.bottomLeftPct ?? 50) + '%',
    transform: 'translateX(-50%)',
    fontSize: (l.seatFontSize || 24) + 'px',
    textAlign: 'center',
    zIndex: 1
  }
})

const BASE_PX_PER_MM = 96 / 25.4

const CAL_KEY_X = 'print_cal_scale_x'
const CAL_KEY_Y = 'print_cal_scale_y'
const calScaleX = ref(parseFloat(localStorage.getItem(CAL_KEY_X)) || 1.0)
const calScaleY = ref(parseFloat(localStorage.getItem(CAL_KEY_Y)) || 1.0)
const showRuler = ref(false)
const showCalibrate = ref(false)
const calTargetMmX = ref(10)
const calTargetMmY = ref(10)
const calMeasuredMmX = ref(null)
const calMeasuredMmY = ref(null)

function saveCalibration() {
  localStorage.setItem(CAL_KEY_X, calScaleX.value.toString())
  localStorage.setItem(CAL_KEY_Y, calScaleY.value.toString())
}

function applyCalibrationX() {
  if (calMeasuredMmX.value && calMeasuredMmX.value > 0) {
    calScaleX.value = calTargetMmX.value / calMeasuredMmX.value
    saveCalibration()
  }
}

function applyCalibrationY() {
  if (calMeasuredMmY.value && calMeasuredMmY.value > 0) {
    calScaleY.value = calTargetMmY.value / calMeasuredMmY.value
    saveCalibration()
  }
}

const calBarStyleX = computed(() => ({
  width: calTargetMmX.value * BASE_PX_PER_MM * calScaleX.value + 'px',
  height: '4px',
  background: 'red',
  margin: '8px 0'
}))

const calBarStyleY = computed(() => ({
  width: '4px',
  height: calTargetMmY.value * BASE_PX_PER_MM * calScaleY.value + 'px',
  background: 'red',
  margin: '0 8px'
}))

// 实际纸张尺寸（A4画布模式用A4，否则用模板尺寸）——标尺和预览页尺寸以此为准
const effectivePageWMm = computed(() => useA4Canvas.value ? A4_W_MM : (resolvedLayout.value.pageWidth || 210))
const effectivePageHMm = computed(() => useA4Canvas.value ? A4_H_MM : (resolvedLayout.value.pageHeight || 297))

const rulerTicks = computed(() => {
  const pmm = BASE_PX_PER_MM
  const wMm = effectivePageWMm.value
  const hMm = effectivePageHMm.value
  const ticks = []
  for (let mm = 0; mm <= wMm; mm += 10) {
    ticks.push({ type: 'h', mm, x: mm * pmm, major: mm % 50 === 0 })
  }
  for (let mm = 0; mm <= hMm; mm += 10) {
    ticks.push({ type: 'v', mm, y: mm * pmm, major: mm % 50 === 0 })
  }
  return ticks
})

const guideLines = computed(() => {
  const pmm = BASE_PX_PER_MM
  const wMm = effectivePageWMm.value
  const hMm = effectivePageHMm.value
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

// 翻转选项（抵消打印机送纸方向差异）
const flipH = computed(() => resolvedLayout.value.flipH === true)
const flipV = computed(() => resolvedLayout.value.flipV === true)

const previewPageStyle = computed(() => {
  const w = effectivePageWMm.value * BASE_PX_PER_MM
  const h = effectivePageHMm.value * BASE_PX_PER_MM
  const fx = flipH.value ? -1 : 1
  const fy = flipV.value ? -1 : 1
  // 翻转时需要平移补偿：scale(-1) 以 top left 为原点会向负方向延伸，需 translate(w) 移回
  const tx = flipH.value ? w : 0
  const ty = flipV.value ? h : 0
  return {
    width: w + 'px',
    height: h + 'px',
    transform: `translate(${tx}px, ${ty}px) scale(${calScaleX.value * fx}, ${calScaleY.value * fy})`,
    transformOrigin: 'top left'
  }
})

const previewWrapperStyle = computed(() => {
  const w = effectivePageWMm.value * BASE_PX_PER_MM * calScaleX.value
  const h = effectivePageHMm.value * BASE_PX_PER_MM * calScaleY.value
  return {
    width: w + 'px',
    height: h + 'px'
  }
})

// 内容缩放层：与后端逻辑一致
// - 默认模式：内容撑满预览页（模板原尺寸）
// - 小纸A4模式：内容不缩放，偏移到小纸在A4走纸槽中的位置（水平+垂直对齐）
const previewScalerStyle = computed(() => {
  const layout = resolvedLayout.value
  const lwMm = layout.pageWidth || 210
  const lhMm = layout.pageHeight || 297
  if (!useA4Canvas.value) {
    return { width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }
  }
  // 小纸A4模式：不缩放，偏移到小纸位置
  const align = layout.smallPaperAlign || 'center'
  let offsetXmm
  if (align === 'left') {
    offsetXmm = 0
  } else if (align === 'right') {
    offsetXmm = A4_W_MM - lwMm
  } else {
    offsetXmm = (A4_W_MM - lwMm) / 2
  }
  // CSS y 向下：top=小纸顶部贴A4顶部 → offsetYmm=0；bottom=小纸底部贴A4底部 → offsetYmm=A4高度-小纸高度
  const vAlign = layout.smallPaperVAlign || 'top'
  const offsetYmm = vAlign === 'bottom' ? (A4_H_MM - lhMm) : 0
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

// 小纸位置指示框（小纸A4模式下显示小纸在A4走纸槽中的位置）
const smallPaperIndicatorStyle = computed(() => {
  if (!smallPaperOnA4.value) return { display: 'none' }
  const layout = resolvedLayout.value
  const lwMm = layout.pageWidth || 210
  const lhMm = layout.pageHeight || 297
  const align = layout.smallPaperAlign || 'center'
  let offsetXmm
  if (align === 'left') {
    offsetXmm = 0
  } else if (align === 'right') {
    offsetXmm = A4_W_MM - lwMm
  } else {
    offsetXmm = (A4_W_MM - lwMm) / 2
  }
  const vAlign = layout.smallPaperVAlign || 'top'
  const offsetYmm = vAlign === 'bottom' ? (A4_H_MM - lhMm) : 0
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

const doPrint = async () => {
  if (!selectedTemplateId.value) {
    ElMessage.warning('请选择打印模板')
    return
  }
  try {
    const records = [{
      id: props.record.id,
      xm1: props.record.xm1,
      xm2: props.record.xm2,
      xm3: props.record.xm3,
      xm4: props.record.xm4,
      xm5: props.record.xm5,
      xm6: props.record.xm6,
      xm7: props.record.xm7,
      xm8: props.record.xm8,
      xm9: props.record.xm9,
      xm10: props.record.xm10,
      fahui_name: props.record.fahui_name,
      zuoweinum: props.record.座次 || props.record.zuoweinum,
      paiwei_type: props.record.paiwei_type,
      shizhu_name: props.record.施主姓名
    }]
    const response = await printerTemplateApi.generatePdf({
      template_id: selectedTemplateId.value,
      records: records
    })
    const blob = new Blob([response], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    if (props.record.id && props.record.prt !== 1) {
      await fahuiRecordApi.update(props.record.id, { prt: 1 })
    }
    ElMessage.success('PDF已生成，请在浏览器中打印')
    dialogVisible.value = false
    emit('printed')
  } catch (error) {
    console.error('打印失败:', error)
    ElMessage.error(error.response?.data?.detail || '打印失败')
  }
}
</script>

<style scoped>
.preview-toolbar { margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.zoom-control { display: flex; align-items: center; gap: 6px; }
.zoom-value { font-size: 12px; color: #409eff; min-width: 36px; text-align: center; }
.calibrate-panel { background: #fff8e6; border: 1px solid #e6a23c; border-radius: 4px; padding: 12px; margin-bottom: 10px; }
.calibrate-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.calibrate-row:last-child { margin-bottom: 0; }
.cal-label { font-weight: bold; font-size: 13px; min-width: 80px; }
.preview-container { background: #e8e8e8; border-radius: 4px; padding: 20px; overflow: auto; max-height: 70vh; }
.preview-page-wrapper { margin: 0 auto; pointer-events: none; }
.preview-page { background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.15); box-sizing: border-box; position: relative; overflow: hidden; pointer-events: auto; }
.ruler-overlay { position: absolute; top: 0; left: 0; pointer-events: none; z-index: 10; }
.preview-bg-image { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; pointer-events: none; }
.preview-content { width: 100%; height: 100%; position: relative; z-index: 1; }
.preview-yangshang-area { display: flex; flex-direction: row-reverse; align-items: flex-start; }
.preview-names-area { display: flex; flex-direction: row-reverse; justify-content: center; align-items: flex-start; }
.preview-bottom { position: absolute; z-index: 1; }
</style>
