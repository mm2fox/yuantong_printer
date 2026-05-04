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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑模板' : '新增模板'" width="1200px" destroy-on-close class="edit-dialog">
      <div class="panel-toggle-bar">
        <el-button size="small" :type="showConfigPanel ? 'primary' : ''" @click="showConfigPanel = !showConfigPanel">📋 配置</el-button>
        <el-button size="small" :type="showPreviewPanel ? 'primary' : ''" @click="showPreviewPanel = !showPreviewPanel">👁 预览</el-button>
        <el-button size="small" :type="showCalibratePanel ? 'primary' : ''" @click="showCalibratePanel = !showCalibratePanel">📏 校准</el-button>
        <span class="preview-info" style="margin-left: 12px;">{{ formData.模板名称 || '未命名模板' }} · {{ layoutConfig.pageWidth }}mm × {{ layoutConfig.pageHeight }}mm</span>
      </div>
      <div class="edit-layout">
        <div class="edit-form-panel" v-show="showConfigPanel">
          <el-form ref="formRef" :model="formData" :rules="formRules" label-width="90px" size="small">
            <el-form-item label="模板名称" prop="模板名称">
              <el-input v-model="formData.模板名称" placeholder="如：延生大牌模板" />
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="模板类型" prop="模板类型">
                  <el-select v-model="formData.模板类型" style="width: 100%" @change="handleTypeChange">
                    <el-option label="延生牌位" value="延生牌位" />
                    <el-option label="往生牌位" value="往生牌位" />
                    <el-option label="佛事牌子" value="佛事牌子" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="牌位类型">
                  <el-select v-model="formData.牌位类型" style="width: 100%" clearable>
                    <el-option label="大牌" value="大牌" />
                    <el-option label="中牌" value="中牌" />
                    <el-option label="小牌" value="小牌" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="是否启用">
              <el-switch v-model="formData.是否启用" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="禁用" />
            </el-form-item>

            <el-divider content-position="left">扫描底图</el-divider>
            <el-form-item label="扫描底图">
              <div class="upload-area">
                <el-upload
                  :auto-upload="false"
                  :show-file-list="false"
                  accept="image/*"
                  :on-change="handleImageChange"
                >
                  <el-button type="primary" size="small">选择图片</el-button>
                </el-upload>
                <el-button type="success" size="small" style="margin-left: 10px" @click="handleOpenScanner" :loading="scanning">扫描仪扫描</el-button>
                <el-button v-if="layoutConfig.backgroundImage" type="danger" size="small" style="margin-left: 10px" @click="removeBackgroundImage">移除</el-button>
                <span v-if="layoutConfig.backgroundImage" style="margin-left: 10px; color: #67c23a; font-size: 12px">已上传底图</span>
                <span v-else style="margin-left: 10px; color: #909399; font-size: 12px">可扫描已有牌位作为底图参考</span>
              </div>
            </el-form-item>
            <el-row v-if="layoutConfig.backgroundImage" :gutter="16">
              <el-col :span="8">
                <el-form-item label="底图透明度">
                  <el-slider v-model="layoutConfig.backgroundOpacity" :min="5" :max="100" :step="5" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="打印底图">
                  <el-switch v-model="layoutConfig.printBackground" active-text="是" inactive-text="否" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="旋转底图">
                  <el-button-group>
                    <el-button size="small" @click="handleRotateImage(90)">左转90°</el-button>
                    <el-button size="small" @click="handleRotateImage(-90)">右转90°</el-button>
                  </el-button-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="打印标尺">
                  <el-switch v-model="layoutConfig.printRuler" active-text="是" inactive-text="否" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider content-position="left">页面设置</el-divider>
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="页面宽度">
                  <el-input-number v-model="layoutConfig.pageWidth" :min="50" :max="2000" style="width: 100%" />
                  <span class="unit">mm</span>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="页面高度">
                  <el-input-number v-model="layoutConfig.pageHeight" :min="50" :max="2000" style="width: 100%" />
                  <span class="unit">mm</span>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="字体">
                  <el-select v-model="layoutConfig.fontFamily" style="width: 100%">
                    <el-option label="华文行楷" value="STXingkai" />
                    <el-option label="宋体" value="SimSun" />
                    <el-option label="黑体" value="SimHei" />
                    <el-option label="楷体" value="KaiTi" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="打印上偏移">
                  <el-input-number v-model="layoutConfig.printOffsetY" :min="-100" :max="100" style="width: 100%" />
                  <span class="unit">mm</span>
                </el-form-item>
              </el-col>
              <el-col :span="16">
                <span style="color: #909399; font-size: 12px; line-height: 32px">正值内容上移，负值下移。用于补偿浏览器打印时内容偏移</span>
              </el-col>
            </el-row>

            <el-divider content-position="left">姓名区域</el-divider>
            <div class="slider-group">
              <div class="slider-item">
                <span class="slider-label">姓名字号</span>
                <el-slider v-model="layoutConfig.nameFontSize" :min="10" :max="100" :show-input="true" :show-input-controls="false" input-size="small" />
              </div>
              <div class="slider-item">
                <span class="slider-label">横向间距</span>
                <el-slider v-model="layoutConfig.nameSpacing" :min="0" :max="80" :show-input="true" :show-input-controls="false" input-size="small" />
              </div>
              <div class="slider-item">
                <span class="slider-label">纵向间距</span>
                <el-slider v-model="layoutConfig.nameCharSpacing" :min="1.0" :max="3.0" :step="0.1" :show-input="true" :show-input-controls="false" input-size="small" />
              </div>
            </div>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="区域上边距">
                  <el-slider v-model="layoutConfig.namesTopPct" :min="0" :max="80" :show-input="true" :show-input-controls="false" input-size="small" />
                  <span class="unit">%页高</span>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="区域左边距">
                  <el-slider v-model="layoutConfig.namesLeftPct" :min="0" :max="80" :show-input="true" :show-input-controls="false" input-size="small" />
                  <span class="unit">%页宽</span>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="区域宽度">
                  <el-slider v-model="layoutConfig.namesWidthPct" :min="10" :max="100" :show-input="true" :show-input-controls="false" input-size="small" />
                  <span class="unit">%页宽</span>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="区域高度">
                  <el-slider v-model="layoutConfig.namesHeightPct" :min="10" :max="100" :show-input="true" :show-input-controls="false" input-size="small" />
                  <span class="unit">%页高</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider content-position="left" v-if="isWangSheng">阳上区域</el-divider>
            <template v-if="isWangSheng">
              <div class="slider-group">
                <div class="slider-item">
                  <span class="slider-label">阳上字号</span>
                  <el-slider v-model="layoutConfig.yangshangFontSize" :min="10" :max="60" :show-input="true" :show-input-controls="false" input-size="small" />
                </div>
                <div class="slider-item">
                  <span class="slider-label">阳上间距</span>
                  <el-slider v-model="layoutConfig.yangshangSpacing" :min="0" :max="40" :show-input="true" :show-input-controls="false" input-size="small" />
                </div>
              </div>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="区域上边距">
                    <el-slider v-model="layoutConfig.yangshangTopPct" :min="0" :max="80" :show-input="true" :show-input-controls="false" input-size="small" />
                    <span class="unit">%页高</span>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="区域左边距">
                    <el-slider v-model="layoutConfig.yangshangLeftPct" :min="0" :max="80" :show-input="true" :show-input-controls="false" input-size="small" />
                    <span class="unit">%页宽</span>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="区域高度">
                    <el-slider v-model="layoutConfig.yangshangHeightPct" :min="10" :max="100" :show-input="true" :show-input-controls="false" input-size="small" />
                    <span class="unit">%页高</span>
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <el-divider content-position="left">底部区域</el-divider>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="座号字号">
                  <el-slider v-model="layoutConfig.seatFontSize" :min="10" :max="48" :show-input="true" :show-input-controls="false" input-size="small" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="区域上边距">
                  <el-slider v-model="layoutConfig.bottomTopPct" :min="50" :max="100" :show-input="true" :show-input-controls="false" input-size="small" />
                  <span class="unit">%页高</span>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="水平位置">
                  <el-slider v-model="layoutConfig.bottomLeftPct" :min="10" :max="90" :show-input="true" :show-input-controls="false" input-size="small" />
                  <span class="unit">%页宽</span>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="显示项目">
              <el-checkbox-group v-model="displayItems">
                <el-checkbox label="姓名" value="shizhu_name" />
                <el-checkbox label="座号" value="seat" />
                <el-checkbox label="法会名称" value="fahui_name" />
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="formData.备注" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>
        </div>
        <div class="edit-preview-panel" v-show="showPreviewPanel">
          <div class="preview-toolbar">
            <div class="zoom-control">
              <el-button size="small" @click="showRuler = !showRuler" :type="showRuler ? 'warning' : ''">标尺</el-button>
              <span class="zoom-value">X:{{ (calScaleX * 100).toFixed(0) }}% Y:{{ (calScaleY * 100).toFixed(0) }}%</span>
            </div>
            <el-button type="primary" size="small" @click="handlePrintPreview">打印</el-button>
          </div>
          <div class="preview-container">
            <div class="preview-page-wrapper" :style="previewWrapperStyle">
              <div class="preview-page" :style="previewPageStyle">
                <img v-if="layoutConfig.backgroundImage" :src="layoutConfig.backgroundImage" class="preview-bg-image" :style="{ opacity: layoutConfig.backgroundOpacity / 100 }" />
                <div class="preview-content" :style="{ fontFamily: layoutConfig.fontFamily }">
                  <div v-if="isWangSheng && displayItems.includes('yangshang')" class="preview-yangshang-area" :style="yangshangAreaStyle">
                    <div :style="{ writingMode: 'vertical-rl', fontSize: layoutConfig.yangshangFontSize + 'px', lineHeight: '1.2' }">阳上</div>
                    <div v-for="(name, idx) in sampleYangshangNames" :key="'ys-'+idx" :style="{ writingMode: 'vertical-rl', fontSize: layoutConfig.yangshangFontSize + 'px', lineHeight: '1.2', letterSpacing: '0.05em' }">{{ name }}</div>
                  </div>
                  <div class="preview-names-area" :style="namesAreaStyle">
                    <div v-for="(name, idx) in alignedSampleNames" :key="'n-'+idx" :style="nameItemStyle">{{ name }}</div>
                  </div>
                  <div v-if="displayItems.includes('seat') || displayItems.includes('fahui_name') || displayItems.includes('shizhu_name')" class="preview-bottom" :style="bottomAreaStyle">
                    <span v-if="displayItems.includes('shizhu_name')">{{ sampleData.shizhu_name }} </span>
                    <span v-if="displayItems.includes('fahui_name')">{{ sampleData.fahui_name }} </span>
                    <span v-if="displayItems.includes('seat')">{{ sampleData.seat }}</span>
                  </div>
                </div>
                <svg v-if="showRuler" class="ruler-overlay" :width="previewPageStyle.width" :height="previewPageStyle.height" xmlns="http://www.w3.org/2000/svg">
                  <line v-for="t in tlRulerTicks.filter(t => t.type === 'h')" :key="'h'+t.mm" :x1="t.x" y1="0" :x2="t.x" :y2="t.major ? 20 : 10" stroke="red" stroke-width="0.5" />
                  <text v-for="t in tlRulerTicks.filter(t => t.type === 'h' && t.mm % 50 === 0)" :key="'ht'+t.mm" :x="t.x" y="30" font-size="10" fill="red" text-anchor="middle">{{ t.mm }}mm</text>
                  <line v-for="t in tlRulerTicks.filter(t => t.type === 'v')" :key="'v'+t.mm" x1="0" :y1="t.y" :x2="t.major ? 20 : 10" :y2="t.y" stroke="red" stroke-width="0.5" />
                  <text v-for="t in tlRulerTicks.filter(t => t.type === 'v' && t.mm % 50 === 0)" :key="'vt'+t.mm" x="30" :y="t.y + 4" font-size="10" fill="red" text-anchor="middle">{{ t.mm }}mm</text>
                  <line v-for="gl in tlGuideLines" :key="gl.key" :x1="gl.x1" :y1="gl.y1" :x2="gl.x2" :y2="gl.y2" stroke="rgba(0,120,255,0.5)" stroke-width="0.8" stroke-dasharray="6,4" />
                </svg>
              </div>
            </div>
          </div>
        </div>
        <div class="edit-calibrate-panel" v-show="showCalibratePanel">
          <div class="calibrate-panel-inner">
            <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #303133;">📏 显示器校准</h4>
            <div class="calibrate-steps">
              <p><strong>第1步：</strong>拿一把尺子放在屏幕前</p>
              <p><strong>第2步：</strong>量红色标定条的实际长度</p>
              <p><strong>第3步：</strong>把量出来的数值填入"实际"输入框</p>
              <p><strong>第4步：</strong>点"应用"，预览就变成真实尺寸了</p>
            </div>
            <div class="calibrate-section">
              <div class="calibrate-label">横向校准</div>
              <div :style="calBarStyleX"></div>
              <div class="calibrate-input-row">
                <span>标称 {{ calTargetMmX }}mm，尺子量出</span>
                <el-input-number v-model="calMeasuredMmX" :min="1" :max="500" :precision="1" size="small" style="width: 90px" />
                <span>mm</span>
              </div>
              <div class="calibrate-btn-row">
                <el-button size="small" type="primary" @click="applyCalibrationX">应用</el-button>
                <el-button size="small" @click="calScaleX = 1.0; saveCalibration()">重置</el-button>
              </div>
            </div>
            <div class="calibrate-section">
              <div class="calibrate-label">纵向校准</div>
              <div :style="calBarStyleY"></div>
              <div class="calibrate-input-row">
                <span>标称 {{ calTargetMmY }}mm，尺子量出</span>
                <el-input-number v-model="calMeasuredMmY" :min="1" :max="500" :precision="1" size="small" style="width: 90px" />
                <span>mm</span>
              </div>
              <div class="calibrate-btn-row">
                <el-button size="small" type="primary" @click="applyCalibrationY">应用</el-button>
                <el-button size="small" @click="calScaleY = 1.0; saveCalibration()">重置</el-button>
              </div>
            </div>
            <div class="calibrate-result">
              <div>横向比例: <strong>{{ (calScaleX * 100).toFixed(1) }}%</strong></div>
              <div>纵向比例: <strong>{{ (calScaleY * 100).toFixed(1) }}%</strong></div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

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
            <img v-if="previewLayoutConfig.backgroundImage" :src="previewLayoutConfig.backgroundImage" class="preview-bg-image" :style="{ opacity: previewLayoutConfig.backgroundOpacity / 100 }" />
            <div class="preview-content" :style="{ fontFamily: previewLayoutConfig.fontFamily }">
              <div v-if="previewIsWangSheng && previewDisplayItems.includes('yangshang')" class="preview-yangshang-area" :style="getYangshangAreaStyle(previewLayoutConfig)">
                <div :style="{ writingMode: 'vertical-rl', fontSize: previewLayoutConfig.yangshangFontSize + 'px', lineHeight: '1.2' }">阳上</div>
                <div v-for="(name, idx) in previewYangshangNames" :key="'ys-'+idx" :style="{ writingMode: 'vertical-rl', fontSize: previewLayoutConfig.yangshangFontSize + 'px', lineHeight: '1.2', letterSpacing: '0.05em' }">{{ name }}</div>
              </div>
              <div class="preview-names-area" :style="getNamesAreaStyle(previewLayoutConfig)">
                <div v-for="(name, idx) in alignedPreviewNames" :key="'n-'+idx" :style="getNameItemStyle(previewLayoutConfig)">{{ name }}</div>
              </div>
              <div v-if="previewDisplayItems.includes('seat') || previewDisplayItems.includes('fahui_name') || previewDisplayItems.includes('shizhu_name')" class="preview-bottom" :style="getBottomAreaStyle(previewLayoutConfig)">
                <span v-if="previewDisplayItems.includes('shizhu_name')">{{ sampleData.shizhu_name }} </span>
                <span v-if="previewDisplayItems.includes('fahui_name')">{{ sampleData.fahui_name }} </span>
                <span v-if="previewDisplayItems.includes('seat')">{{ sampleData.seat }}</span>
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

    <el-dialog v-model="scannerVisible" title="扫描仪" width="450px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="扫描仪">
          <el-select v-model="scannerDeviceId" placeholder="选择扫描仪" style="width: 100%" :loading="scannerListLoading">
            <el-option v-for="dev in scannerDevices" :key="dev.id" :label="dev.name" :value="dev.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="分辨率">
          <el-select v-model="scanResolution" style="width: 100%">
            <el-option label="150 DPI (快速)" :value="150" />
            <el-option label="200 DPI (标准)" :value="200" />
            <el-option label="300 DPI (高清)" :value="300" />
            <el-option label="600 DPI (超清)" :value="600" />
          </el-select>
        </el-form-item>
        <el-form-item label="色彩模式">
          <el-select v-model="scanColorMode" style="width: 100%">
            <el-option label="彩色" :value="1" />
            <el-option label="灰度" :value="2" />
            <el-option label="黑白" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="自动旋转">
          <el-switch v-model="scanAutoRotate" active-text="横图自动转竖" inactive-text="保持原样" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scannerVisible = false">取消</el-button>
        <el-button type="primary" @click="handleScan" :loading="scanning">开始扫描</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { printerTemplateApi } from '@/api/printerTemplates'
import { scannerApi } from '@/api/scanner'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const previewVisible = ref(false)
const scanning = ref(false)
const scannerVisible = ref(false)
const scannerDevices = ref([])
const scannerDeviceId = ref('')
const scannerListLoading = ref(false)
const scanResolution = ref(200)
const scanColorMode = ref(1)
const scanAutoRotate = ref(true)

const formData = reactive({
  id: null,
  模板名称: '',
  模板类型: '',
  牌位类型: '',
  布局配置: '',
  是否启用: 1,
  备注: ''
})

const defaultLayoutConfig = {
  pageWidth: 210,
  pageHeight: 297,
  fontFamily: 'STXingkai',
  nameFontSize: 52,
  nameSpacing: 20,
  nameCharSpacing: 1.3,
  namesTopPct: 25,
  namesLeftPct: 10,
  namesWidthPct: 80,
  namesHeightPct: 55,
  yangshangFontSize: 18,
  yangshangSpacing: 5,
  seatFontSize: 24,
  bottomTopPct: 90,
  bottomLeftPct: 50,
  backgroundImage: '',
  backgroundOpacity: 30,
  printBackground: false,
  printRuler: false,
  printOffsetY: 0
}

const layoutConfig = reactive({ ...defaultLayoutConfig })

const contentTemplate = reactive({
  namesTitle: '佛光注照'
})

const displayItems = ref(['seat', 'fahui_name'])

const sampleData = {
  fahui_name: '示例法会',
  seat: '0001',
  shizhu_name: '张施主',
  names_yansheng: ['张三', '李四', '王五'],
  names_wangsheng_jieyin: ['赵六', '钱七', '孙八'],
  names_wangsheng_yangshang: ['周九', '吴十']
}

const isWangSheng = computed(() => formData.模板类型 === '往生牌位')

const sampleNames = computed(() => {
  if (isWangSheng.value) return sampleData.names_wangsheng_jieyin
  return sampleData.names_yansheng
})

const sampleYangshangNames = computed(() => {
  if (!isWangSheng.value) return []
  return sampleData.names_wangsheng_yangshang
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

const parsedSampleNames = computed(() => {
  return sampleNames.value.map(n => splitNameSuffix(n))
})

const maxSampleNamePartLen = computed(() => {
  return Math.max(...parsedSampleNames.value.map(n => n.namePart.length), 0)
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

const alignedSampleNames = computed(() => {
  return parsedSampleNames.value.map(parsed => {
    const padded = padNamePart(parsed.namePart, maxSampleNamePartLen.value)
    return padded + (parsed.suffix ? parsed.suffix : '')
  })
})

const parsedPreviewNames = computed(() => {
  return previewNames.value.map(n => splitNameSuffix(n))
})

const maxPreviewNamePartLen = computed(() => {
  return Math.max(...parsedPreviewNames.value.map(n => n.namePart.length), 0)
})

const alignedPreviewNames = computed(() => {
  return parsedPreviewNames.value.map(parsed => {
    const padded = padNamePart(parsed.namePart, maxPreviewNamePartLen.value)
    return padded + (parsed.suffix ? parsed.suffix : '')
  })
})

const namesAreaStyle = computed(() => getNamesAreaStyle(layoutConfig))
const yangshangAreaStyle = computed(() => getYangshangAreaStyle(layoutConfig))
const nameItemStyle = computed(() => getNameItemStyle(layoutConfig))
const bottomAreaStyle = computed(() => getBottomAreaStyle(layoutConfig))

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
    alignItems: 'flex-start',
    boxSizing: 'border-box'
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
    height: (cfg.yangshangHeightPct ?? 55) + '%',
    display: 'flex',
    flexDirection: 'row-reverse',
    alignItems: 'flex-start',
    boxSizing: 'border-box'
  }
}

const getNameItemStyle = (cfg) => ({
  writingMode: 'vertical-rl',
  fontSize: cfg.nameFontSize + 'px',
  lineHeight: '1.2',
  letterSpacing: ((cfg.nameCharSpacing || 1.3) - 1.0) + 'em',
  margin: '0 ' + cfg.nameSpacing / 2 + 'px'
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

const CAL_KEY_X = 'print_cal_scale_x'
const CAL_KEY_Y = 'print_cal_scale_y'
const calScaleX = ref(parseFloat(localStorage.getItem(CAL_KEY_X)) || 1.0)
const calScaleY = ref(parseFloat(localStorage.getItem(CAL_KEY_Y)) || 1.0)
const showRuler = ref(false)
const showConfigPanel = ref(true)
const showPreviewPanel = ref(true)
const showCalibratePanel = ref(false)
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

const BASE_PX_PER_MM = 96 / 25.4

const tlPxPerMmX = computed(() => BASE_PX_PER_MM)
const tlPxPerMmY = computed(() => BASE_PX_PER_MM)

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

const tlRulerTicks = computed(() => {
  const pmm = BASE_PX_PER_MM
  const wMm = layoutConfig.pageWidth || 210
  const hMm = layoutConfig.pageHeight || 297
  const ticks = []
  for (let mm = 0; mm <= wMm; mm += 10) {
    ticks.push({ type: 'h', mm, x: mm * pmm, major: mm % 50 === 0 })
  }
  for (let mm = 0; mm <= hMm; mm += 10) {
    ticks.push({ type: 'v', mm, y: mm * pmm, major: mm % 50 === 0 })
  }
  return ticks
})

const tlGuideLines = computed(() => {
  const pmm = BASE_PX_PER_MM
  const w = layoutConfig.pageWidth * pmm
  const h = layoutConfig.pageHeight * pmm
  const wMm = layoutConfig.pageWidth || 210
  const hMm = layoutConfig.pageHeight || 297
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

const previewPageStyle = computed(() => {
  const w = layoutConfig.pageWidth * BASE_PX_PER_MM
  const h = layoutConfig.pageHeight * BASE_PX_PER_MM
  return {
    width: w + 'px',
    height: h + 'px',
    transform: `scale(${calScaleX.value}, ${calScaleY.value})`,
    transformOrigin: 'top left'
  }
})

const previewWrapperStyle = computed(() => {
  const w = layoutConfig.pageWidth * BASE_PX_PER_MM * calScaleX.value
  const h = layoutConfig.pageHeight * BASE_PX_PER_MM * calScaleY.value
  return {
    width: w + 'px',
    height: h + 'px'
  }
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

const dialogRulerTicks = computed(() => {
  const pmm = BASE_PX_PER_MM
  const wMm = previewLayoutConfig.pageWidth || 210
  const hMm = previewLayoutConfig.pageHeight || 297
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
  const w = previewLayoutConfig.pageWidth * pmm
  const h = previewLayoutConfig.pageHeight * pmm
  const wMm = previewLayoutConfig.pageWidth || 210
  const hMm = previewLayoutConfig.pageHeight || 297
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
  const w = previewLayoutConfig.pageWidth * BASE_PX_PER_MM
  const h = previewLayoutConfig.pageHeight * BASE_PX_PER_MM
  return {
    width: w + 'px',
    height: h + 'px',
    transform: `scale(${calScaleX.value}, ${calScaleY.value})`,
    transformOrigin: 'top left'
  }
})

const previewWrapperStyleForDialog = computed(() => {
  const w = previewLayoutConfig.pageWidth * BASE_PX_PER_MM * calScaleX.value
  const h = previewLayoutConfig.pageHeight * BASE_PX_PER_MM * calScaleY.value
  return {
    width: w + 'px',
    height: h + 'px'
  }
})

const formRules = {
  模板名称: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  模板类型: [{ required: true, message: '请选择模板类型', trigger: 'change' }]
}

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

const resetForm = () => {
  Object.assign(formData, {
    id: null,
    模板名称: '',
    模板类型: '',
    牌位类型: '',
    布局配置: '',
    是否启用: 1,
    备注: ''
  })
  Object.assign(layoutConfig, { ...defaultLayoutConfig })
  Object.assign(contentTemplate, { namesTitle: '佛光注照' })
  displayItems.value = ['seat', 'fahui_name']
}

const handleTypeChange = (val) => {
  if (val === '延生牌位') {
    contentTemplate.namesTitle = '佛光注照'
    displayItems.value = ['seat', 'fahui_name']
  } else if (val === '往生牌位') {
    contentTemplate.namesTitle = '佛光接引'
    displayItems.value = ['seat', 'fahui_name']
  } else if (val === '佛事牌子') {
    contentTemplate.namesTitle = '佛力超度'
    displayItems.value = ['shizhu_name']
  }
}

const handleAdd = () => {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

const loadConfig = (row) => {
  if (row.布局配置) {
    try {
      const config = JSON.parse(row.布局配置)
      if (config.layout) {
        const migrated = { ...defaultLayoutConfig, ...config.layout }
        migrateOldConfig(migrated)
        Object.assign(layoutConfig, migrated)
      }
      if (config.content) Object.assign(contentTemplate, config.content)
      if (config.displayItems) displayItems.value = config.displayItems
    } catch (e) {
      console.error('解析布局配置失败:', e)
    }
  }
}

const handleEdit = (row) => {
  resetForm()
  isEdit.value = true
  Object.assign(formData, {
    id: row.id,
    模板名称: row.模板名称,
    模板类型: row.模板类型,
    牌位类型: row.牌位类型,
    是否启用: row.是否启用,
    备注: row.备注
  })
  loadConfig(row)
  dialogVisible.value = true
}

const handleCopy = (row) => {
  resetForm()
  isEdit.value = false
  Object.assign(formData, {
    模板名称: row.模板名称 + ' (副本)',
    模板类型: row.模板类型,
    牌位类型: row.牌位类型,
    是否启用: 1,
    备注: row.备注
  })
  loadConfig(row)
  dialogVisible.value = true
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

const handleImageChange = async (uploadFile) => {
  try {
    const res = await printerTemplateApi.uploadImage(uploadFile.raw)
    layoutConfig.backgroundImage = res.url
    applyImageSize(res)
    ElMessage.success('底图上传成功，已自动调整页面尺寸')
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('底图上传失败')
  }
}

const removeBackgroundImage = () => {
  layoutConfig.backgroundImage = ''
}

const handleRotateImage = async (angle) => {
  if (!layoutConfig.backgroundImage) return
  try {
    const res = await printerTemplateApi.rotateImage({
      url: layoutConfig.backgroundImage,
      angle: angle
    })
    applyImageSize(res)
    ElMessage.success(angle === 90 ? '已左转90°' : '已右转90°')
  } catch (error) {
    console.error('旋转失败:', error)
    ElMessage.error('旋转底图失败')
  }
}

const applyImageSize = (res) => {
  if (res.mmWidth && res.mmHeight) {
    layoutConfig.pageWidth = Math.round(res.mmWidth)
    layoutConfig.pageHeight = Math.round(res.mmHeight)
  }
  if (res.url) {
    layoutConfig.backgroundImage = res.url + '?t=' + Date.now()
  }
  adjustFontSizeForPage()
}

const adjustFontSizeForPage = () => {
  const area = layoutConfig.pageWidth * layoutConfig.pageHeight
  const ratio = area / (210 * 297)
  const scale = Math.sqrt(ratio)
  layoutConfig.nameFontSize = Math.round(52 * scale)
  layoutConfig.yangshangFontSize = Math.round(18 * scale)
  layoutConfig.seatFontSize = Math.round(24 * scale)
}

const handleOpenScanner = async () => {
  scannerVisible.value = true
  scannerListLoading.value = true
  try {
    const devices = await scannerApi.getDevices()
    scannerDevices.value = devices
    if (devices.length > 0 && !scannerDeviceId.value) {
      scannerDeviceId.value = devices[0].id
    }
  } catch (error) {
    console.error('获取扫描仪列表失败:', error)
    ElMessage.warning(error.response?.data?.detail || '获取扫描仪列表失败，请确认已连接扫描仪')
  } finally {
    scannerListLoading.value = false
  }
}

const handleScan = async () => {
  scanning.value = true
  try {
    const res = await scannerApi.scan({
      device_id: scannerDeviceId.value || undefined,
      resolution: scanResolution.value,
      color_mode: scanColorMode.value,
      auto_rotate: scanAutoRotate.value
    })
    layoutConfig.backgroundImage = res.url
    applyImageSize(res)
    ElMessage.success('扫描成功，已自动调整页面尺寸')
    scannerVisible.value = false
  } catch (error) {
    console.error('扫描失败:', error)
    ElMessage.error(error.response?.data?.detail || '扫描失败')
  } finally {
    scanning.value = false
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
    const records = [{
      xm1: names[0] || '',
      xm2: names[1] || '',
      xm3: names[2] || '',
      xm4: yangshangNames[0] || '',
      xm5: yangshangNames[1] || '',
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

const handlePrintPreview = () => {
  const names = isWangSheng.value ? sampleData.names_wangsheng_jieyin : sampleData.names_yansheng
  const yangshangNames = isWangSheng.value ? sampleData.names_wangsheng_yangshang : []
  const config = {
    layout: { ...layoutConfig },
    content: { ...contentTemplate },
    displayItems: displayItems.value,
    _template_type: formData.模板类型 || (isWangSheng.value ? '往生牌位' : '延生牌位'),
    _templateName: formData.模板名称
  }
  openPdfFromConfig(config, names, yangshangNames, sampleData.seat, sampleData.fahui_name, sampleData.shizhu_name)
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

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const config = {
          layout: { ...layoutConfig },
          content: { ...contentTemplate },
          displayItems: displayItems.value
        }
        const submitData = { ...formData, 布局配置: JSON.stringify(config) }
        if (isEdit.value) {
          await printerTemplateApi.update(formData.id, submitData)
          ElMessage.success('更新成功')
        } else {
          await printerTemplateApi.create(submitData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchData()
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error('操作失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

onMounted(() => { fetchData() })
</script>

<style scoped>
.template-list { height: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.unit { margin-left: 5px; color: #909399; font-size: 12px; }
.upload-area { display: flex; align-items: center; }
.edit-layout { display: flex; gap: 12px; height: 70vh; }
.edit-form-panel { flex: 1 1 380px; min-width: 320px; overflow-y: auto; padding-right: 8px; border-right: 1px solid #ebeef5; }
.edit-preview-panel { flex: 1 1 400px; min-width: 0; display: flex; flex-direction: column; }
.edit-calibrate-panel { flex: 0 0 220px; overflow-y: auto; border-left: 1px solid #ebeef5; padding-left: 8px; }
.calibrate-panel-inner { padding: 4px 0; }
.calibrate-section { margin-bottom: 16px; padding: 10px; background: #f5f7fa; border-radius: 6px; }
.calibrate-label { font-weight: bold; font-size: 13px; margin-bottom: 8px; color: #303133; }
.calibrate-input-row { display: flex; align-items: center; gap: 4px; margin-top: 8px; font-size: 12px; }
.calibrate-btn-row { margin-top: 8px; display: flex; gap: 6px; }
.calibrate-result { margin-top: 12px; padding: 8px; background: #ecf5ff; border-radius: 4px; font-size: 12px; line-height: 1.8; }
.panel-toggle-bar { display: flex; align-items: center; gap: 4px; margin-bottom: 12px; padding: 6px 10px; background: #f5f7fa; border-radius: 6px; }
.calibrate-steps { background: #fff8e6; border: 1px solid #e6a23c; border-radius: 6px; padding: 10px; margin-bottom: 12px; }
.calibrate-steps p { margin: 0 0 4px 0; font-size: 12px; line-height: 1.6; color: #606266; }
.calibrate-steps p:last-child { margin-bottom: 0; }
.slider-group { padding: 0 10px; }
.slider-item { display: flex; align-items: center; margin-bottom: 4px; }
.slider-label { width: 70px; font-size: 13px; color: #606266; flex-shrink: 0; }
.slider-item :deep(.el-slider) { flex: 1; }
.slider-item :deep(.el-slider__runway) { margin: 0; }
.preview-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 6px 10px; background: #f5f7fa; border-radius: 4px; gap: 8px; }
.zoom-control { display: flex; align-items: center; gap: 6px; flex: 1; justify-content: center; }
.zoom-label { font-size: 12px; color: #606266; white-space: nowrap; }
.zoom-value { font-size: 12px; color: #409eff; min-width: 36px; text-align: center; }
.preview-info { color: #606266; font-size: 13px; }
.preview-container { flex: 1; display: flex; justify-content: center; align-items: flex-start; background: #e8e8e8; border-radius: 4px; padding: 15px; overflow: auto; }
.preview-page-wrapper { flex-shrink: 0; pointer-events: none; }
.preview-page { background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,0.15); box-sizing: border-box; position: relative; overflow: hidden; pointer-events: auto; }
.ruler-overlay { position: absolute; top: 0; left: 0; pointer-events: none; z-index: 10; }
.preview-bg-image { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; pointer-events: none; }
.preview-content { width: 100%; height: 100%; position: relative; z-index: 1; }
.preview-yangshang-area { display: flex; flex-direction: row-reverse; align-items: flex-start; }
.preview-names-area { display: flex; flex-direction: row-reverse; justify-content: center; align-items: flex-start; }
.preview-bottom { position: absolute; z-index: 1; }
</style>
