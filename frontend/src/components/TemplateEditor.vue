<template>
  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑模板' : '新增模板'" width="1200px" destroy-on-close class="edit-dialog" @close="handleClose">
    <div class="panel-toggle-bar">
      <el-button size="small" :type="showConfigPanel ? 'primary' : ''" @click="showConfigPanel = !showConfigPanel">📋 配置</el-button>
      <el-button size="small" :type="showPreviewPanel ? 'primary' : ''" @click="showPreviewPanel = !showPreviewPanel">👁 预览</el-button>
      <el-button size="small" :type="showCalibratePanel ? 'primary' : ''" @click="showCalibratePanel = !showCalibratePanel">📏 校准</el-button>
      <span class="preview-info" style="margin-left: 12px;">{{ formData.模板名称 || '未命名模板' }} · {{ layoutConfig.pageWidth }}mm × {{ layoutConfig.pageHeight }}mm</span>
      <el-tag v-if="hasRecordData" type="success" size="small" style="margin-left: 8px;">已载入打印数据</el-tag>
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
            <el-col :span="24">
              <el-form-item label="输出模式">
                <el-radio-group v-model="outputMode" @change="onOutputModeChange">
                  <el-radio label="original">实际尺寸（PDF=模板尺寸，打印机走纸尺寸需=模板尺寸）</el-radio>
                  <el-radio label="smallpaper">小纸A4对齐（打印机驱动选A4，实际送小纸，内容不缩放）</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row v-if="layoutConfig.smallPaperOnA4" :gutter="16">
            <el-col :span="12">
              <el-form-item label="水平对齐">
                <el-radio-group v-model="layoutConfig.smallPaperAlign">
                  <el-radio label="left">左</el-radio>
                  <el-radio label="center">中</el-radio>
                  <el-radio label="right">右</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="垂直对齐">
                <el-radio-group v-model="layoutConfig.smallPaperVAlign">
                  <el-radio label="top">上</el-radio>
                  <el-radio label="bottom">下</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row v-if="layoutConfig.smallPaperOnA4" :gutter="16">
            <el-col :span="24">
              <span style="color: #909399; font-size: 12px; line-height: 32px">小纸A4对齐模式：PDF画布=A4，内容按上方模板尺寸（如87×220mm）不缩放绘制，偏移到小纸在A4走纸槽中的位置。打印机驱动选A4走纸，实际送小纸。水平/垂直对齐决定小纸在A4槽中的位置。预览中绿色虚线框=小纸实际位置。</span>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="24">
              <el-form-item label="翻转">
                <el-checkbox v-model="layoutConfig.flipH">左右翻转</el-checkbox>
                <el-checkbox v-model="layoutConfig.flipV">上下翻转</el-checkbox>
                <span style="color: #909399; font-size: 12px; margin-left: 12px;">不同打印机送纸方向不同，可能导致实际打印结果和预览呈镜像或颠倒。勾选对应翻转可抵消打印机方向差异。</span>
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
              <el-slider v-model="layoutConfig.nameCharSpacing" :min="1.0" :max="3.0" :step="0.1" :show-input="true" :show-input-controls="false" input-size="small" :disabled="layoutConfig.nameAutoAdjust" />
            </div>
          </div>
          <el-form-item label="纵向对齐">
            <el-radio-group v-model="layoutConfig.nameVertAlign" size="small" :disabled="!layoutConfig.nameAutoAdjust">
              <el-radio-button label="top">靠上</el-radio-button>
              <el-radio-button label="center">居中</el-radio-button>
            </el-radio-group>
            <el-switch v-model="layoutConfig.nameAutoAdjust" active-text="自动间距" style="margin-left: 12px;" />
            <span style="margin-left: 8px; color: #909399; font-size: 12px;">{{ layoutConfig.nameAutoAdjust ? '靠上=撑满区域，居中=居中排列' : '手动设置纵向间距，与之前一致' }}</span>
          </el-form-item>
          <el-form-item label="自动补齐">
            <el-switch v-model="layoutConfig.autoPadNames" active-text="对齐补空格" inactive-text="保留原始" />
            <span style="margin-left: 8px; color: #909399; font-size: 12px;">关闭后姓名按原始内容打印，不自动补空格对齐</span>
          </el-form-item>
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
                <span class="slider-label">横向间距</span>
                <el-slider v-model="layoutConfig.yangshangSpacing" :min="0" :max="40" :show-input="true" :show-input-controls="false" input-size="small" />
              </div>
              <div class="slider-item">
                <span class="slider-label">纵向间距</span>
                <el-slider v-model="layoutConfig.yangshangCharSpacing" :min="1.0" :max="3.0" :step="0.1" :show-input="true" :show-input-controls="false" input-size="small" :disabled="layoutConfig.yangshangAutoAdjust || layoutConfig.yangshangRows === 2" />
              </div>
            </div>
            <el-form-item label="纵向对齐">
              <el-radio-group v-model="layoutConfig.yangshangVertAlign" size="small" :disabled="!layoutConfig.yangshangAutoAdjust || layoutConfig.yangshangRows === 2">
                <el-radio-button label="top">靠上</el-radio-button>
                <el-radio-button label="center">居中</el-radio-button>
              </el-radio-group>
              <el-switch v-model="layoutConfig.yangshangAutoAdjust" active-text="自动间距" style="margin-left: 12px;" :disabled="layoutConfig.yangshangRows === 2" />
              <span style="margin-left: 8px; color: #909399; font-size: 12px;">{{ layoutConfig.yangshangRows === 2 ? '两排模式固定靠上/靠下' : (layoutConfig.yangshangAutoAdjust ? '靠上=撑满区域，居中=居中排列' : '手动设置纵向间距，与之前一致') }}</span>
            </el-form-item>
            <el-form-item label="自动补齐">
              <el-switch v-model="layoutConfig.autoPadYangshang" active-text="对齐补空格" inactive-text="保留原始" />
              <span style="margin-left: 8px; color: #909399; font-size: 12px;">关闭后阳上按原始内容打印，不自动补空格对齐</span>
            </el-form-item>
            <el-form-item label="排列排数">
              <el-radio-group v-model="layoutConfig.yangshangRows">
                <el-radio :label="1">一排</el-radio>
                <el-radio :label="2">两排（上下错开）</el-radio>
              </el-radio-group>
              <span style="margin-left: 8px; color: #909399; font-size: 12px;">两排时第1/3/5…个在上排，第2/4/6…个在下排</span>
            </el-form-item>
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
                <el-form-item label="区域宽度">
                  <el-slider v-model="layoutConfig.yangshangWidthPct" :min="10" :max="100" :show-input="true" :show-input-controls="false" input-size="small" />
                  <span class="unit">%页宽</span>
                </el-form-item>
              </el-col>
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
              <el-checkbox v-if="isWangSheng" label="阳上" value="yangshang" />
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
              <div class="small-paper-indicator" :style="tlSmallPaperIndicatorStyle"></div>
              <div class="preview-scaler" :style="tlPreviewScalerStyle">
                <img v-if="layoutConfig.backgroundImage" :src="layoutConfig.backgroundImage" class="preview-bg-image" :style="{ opacity: layoutConfig.backgroundOpacity / 100 }" />
                <div class="preview-content" :style="{ fontFamily: layoutConfig.fontFamily }">
                  <div v-if="isWangSheng && displayItems.includes('yangshang')" class="preview-yangshang-area" :style="yangshangAreaStyle">
                    <span class="capacity-badge" :style="{ background: '#67c23a' }">横 {{ charCapacityOf(layoutConfig, 'yangshang').horz }} × 竖 {{ charCapacityOf(layoutConfig, 'yangshang').vert }} 字{{ layoutConfig.yangshangRows === 2 ? ' / 行' : '' }}</span>
                  <div v-for="(pair, pIdx) in yangshangPairs(alignedSampleYangshangNames, layoutConfig.yangshangRows)" :key="'ysp-'+pIdx" class="ys-pair" :style="ysPairStyle(layoutConfig)">
                    <div v-for="item in pair" :key="'ys-'+item.idx" :style="(layoutConfig.yangshangRows === 1 && layoutConfig.yangshangAutoAdjust && layoutConfig.yangshangVertAlign !== 'center') ? getYangshangFillItemStyle(layoutConfig) : getYangshangItemStyle(layoutConfig, item.idx)" class="editable-cell" contenteditable="plaintext-only" @focus="onSampleFocus($event, item.idx, 'yangshang')" @blur="onSampleBlur($event, item.idx, 'yangshang')">
                      <template v-if="layoutConfig.yangshangRows === 1 && layoutConfig.yangshangAutoAdjust && layoutConfig.yangshangVertAlign !== 'center'"><span v-for="(ch, ci) in item.name" :key="ci" :style="{ fontSize: layoutConfig.yangshangFontSize + 'px', lineHeight: '1' }">{{ ch }}</span></template>
                      <template v-else>{{ item.name }}</template>
                    </div>
                  </div>
                  <div class="add-name-btn" :style="{ writingMode: 'vertical-rl', fontSize: layoutConfig.yangshangFontSize + 'px', lineHeight: '1.2', color: '#c0c4cc', cursor: 'pointer', border: '1px dashed #dcdfe6', padding: '2px 4px' }" @click="addSampleName('yangshang')">+ 添加</div>
                </div>
                  <div class="preview-names-area" :style="namesAreaStyle">
                    <span class="capacity-badge" :style="{ background: '#f56c6c' }">横 {{ charCapacityOf(layoutConfig, 'name').horz }} × 竖 {{ charCapacityOf(layoutConfig, 'name').vert }} 字</span>
                    <div v-for="(name, idx) in alignedSampleNames" :key="'n-'+idx" :style="(layoutConfig.nameAutoAdjust && layoutConfig.nameVertAlign !== 'center') ? getNameFillItemStyle(layoutConfig) : nameItemStyle" class="editable-cell" contenteditable="plaintext-only" @focus="onSampleFocus($event, idx, 'name')" @blur="onSampleBlur($event, idx, 'name')">
                      <template v-if="layoutConfig.nameAutoAdjust && layoutConfig.nameVertAlign !== 'center'"><span v-for="(ch, ci) in name" :key="ci" :style="{ fontSize: layoutConfig.nameFontSize + 'px', lineHeight: '1' }">{{ ch }}</span></template>
                      <template v-else>{{ name }}</template>
                    </div>
                    <div class="add-name-btn" :style="nameItemStyle" style="position: absolute; left: 0; top: 0; z-index: 5; color: #c0c4cc; cursor: pointer; border: 1px dashed #dcdfe6; padding: 2px 4px;" @click="addSampleName('name')">+ 添加</div>
                  </div>
                  <div v-if="displayItems.includes('seat') || displayItems.includes('fahui_name') || displayItems.includes('shizhu_name')" class="preview-bottom" :style="bottomAreaStyle">
                    <span v-if="displayItems.includes('shizhu_name')" class="editable-cell" contenteditable="plaintext-only" @blur="onBottomBlur($event, 'shizhu_name')">{{ sampleData.shizhu_name }} </span>
                    <span v-if="displayItems.includes('fahui_name')" class="editable-cell" contenteditable="plaintext-only" @blur="onBottomBlur($event, 'fahui_name')">{{ sampleData.fahui_name }} </span>
                    <span v-if="displayItems.includes('seat')" class="editable-cell" contenteditable="plaintext-only" @blur="onBottomBlur($event, 'seat')">{{ sampleData.seat }}</span>
                  </div>
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

    <el-dialog v-model="scannerVisible" title="扫描仪" width="450px" destroy-on-close append-to-body>
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
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { printerTemplateApi } from '@/api/printerTemplates'
import { scannerApi } from '@/api/scanner'

const props = defineProps({
  visible: { type: Boolean, default: false },
  template: { type: Object, default: null },
  copyMode: { type: Boolean, default: false },
  initialSampleData: { type: Object, default: null }
})

const emit = defineEmits(['update:visible', 'saved'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const isEdit = computed(() => !!props.template && !props.copyMode)

const hasRecordData = computed(() => !!props.initialSampleData)

const handleClose = () => {
  emit('update:visible', false)
}

const submitLoading = ref(false)
const formRef = ref(null)

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

const layoutConfig = reactive({ ...defaultLayoutConfig })

const outputMode = computed({
  get: () => layoutConfig.smallPaperOnA4 ? 'smallpaper' : 'original',
  set: (val) => { layoutConfig.smallPaperOnA4 = (val === 'smallpaper') }
})
const onOutputModeChange = (val) => {
  layoutConfig.smallPaperOnA4 = (val === 'smallpaper')
}

const contentTemplate = reactive({ namesTitle: '佛光注照' })

const displayItems = ref(['seat', 'fahui_name'])

const defaultSampleData = () => ({
  fahui_name: '示例法会',
  seat: '0001',
  shizhu_name: '张施主',
  names_yansheng: ['张三', '李四', '王五'],
  names_wangsheng_jieyin: ['赵六', '钱七', '孙八', '李九'],
  names_wangsheng_yangshang: ['周一', '吴二', '郑三']
})

const sampleData = reactive(defaultSampleData())

const isWangSheng = computed(() => formData.模板类型 === '往生牌位')

const sampleNames = computed(() => {
  if (isWangSheng.value) return sampleData.names_wangsheng_jieyin
  return sampleData.names_yansheng
})

const sampleYangshangNames = computed(() => {
  if (!isWangSheng.value) return []
  return sampleData.names_wangsheng_yangshang
})

const onSampleFocus = (e, idx, type) => {
  let arr
  if (type === 'name') arr = sampleNames.value
  else if (type === 'yangshang') arr = sampleYangshangNames.value
  if (arr) e.target.textContent = arr[idx] || ''
}

const onSampleBlur = (e, idx, type) => {
  const newText = e.target.textContent.trim()
  let arr
  if (type === 'name') arr = sampleNames.value
  else if (type === 'yangshang') arr = sampleYangshangNames.value
  if (!arr) return
  if (newText) {
    arr[idx] = newText
  } else {
    arr.splice(idx, 1)
  }
}

const onBottomBlur = (e, field) => {
  sampleData[field] = e.target.textContent.trim()
}

const addSampleName = (type) => {
  if (type === 'name') {
    if (isWangSheng.value) sampleData.names_wangsheng_jieyin.push('新名')
    else sampleData.names_yansheng.push('新名')
  } else if (type === 'yangshang') {
    sampleData.names_wangsheng_yangshang.push('新名')
  }
}

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

const parsedSampleNames = computed(() => sampleNames.value.map(n => splitNameSuffix(n)))
const maxSampleNamePartLen = computed(() => Math.max(...parsedSampleNames.value.map(n => n.namePart.length), 0))

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

const alignedSampleNames = computed(() => {
  if (layoutConfig.autoPadNames === false) {
    return sampleNames.value.map(normalizeRawName)
  }
  return parsedSampleNames.value.map(parsed => {
    const padded = padNamePart(parsed.namePart, maxSampleNamePartLen.value)
    return padded + (parsed.suffix ? parsed.suffix : '')
  })
})

const parsedSampleYangshangNames = computed(() => sampleYangshangNames.value.map(n => splitNameSuffix(n)))
const maxSampleYangshangNamePartLen = computed(() => Math.max(...parsedSampleYangshangNames.value.map(n => n.namePart.length), 0))

const alignedSampleYangshangNames = computed(() => {
  if (layoutConfig.autoPadYangshang === false) {
    return sampleYangshangNames.value.map(normalizeRawName)
  }
  return parsedSampleYangshangNames.value.map(parsed => {
    const padded = padNamePart(parsed.namePart, maxSampleYangshangNamePartLen.value)
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

const namesAreaStyle = computed(() => getNamesAreaStyle(layoutConfig))
const yangshangAreaStyle = computed(() => getYangshangAreaStyle(layoutConfig))
const nameItemStyle = computed(() => getNameItemStyle(layoutConfig))
const bottomAreaStyle = computed(() => getBottomAreaStyle(layoutConfig))

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
const A4_W_MM = 210
const A4_H_MM = 297

const tlUseA4Canvas = computed(() => layoutConfig.smallPaperOnA4)
const tlEffectiveWMm = computed(() => tlUseA4Canvas.value ? A4_W_MM : (layoutConfig.pageWidth || 210))
const tlEffectiveHMm = computed(() => tlUseA4Canvas.value ? A4_H_MM : (layoutConfig.pageHeight || 297))

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

const tlPreviewScalerStyle = computed(() => {
  const lwMm = layoutConfig.pageWidth || 210
  const lhMm = layoutConfig.pageHeight || 297
  if (!tlUseA4Canvas.value) {
    return { width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }
  }
  const { offsetXmm, offsetYmm } = computeSmallPaperOffset(layoutConfig)
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

const tlSmallPaperIndicatorStyle = computed(() => {
  if (!layoutConfig.smallPaperOnA4) return { display: 'none' }
  const lwMm = layoutConfig.pageWidth || 210
  const lhMm = layoutConfig.pageHeight || 297
  const { offsetXmm, offsetYmm } = computeSmallPaperOffset(layoutConfig)
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
  const wMm = tlEffectiveWMm.value
  const hMm = tlEffectiveHMm.value
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
  const wMm = tlEffectiveWMm.value
  const hMm = tlEffectiveHMm.value
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

const previewPageStyle = computed(() => {
  const w = tlEffectiveWMm.value * BASE_PX_PER_MM
  const h = tlEffectiveHMm.value * BASE_PX_PER_MM
  const fx = layoutConfig.flipH ? -1 : 1
  const fy = layoutConfig.flipV ? -1 : 1
  const tx = layoutConfig.flipH ? w : 0
  const ty = layoutConfig.flipV ? h : 0
  return {
    width: w + 'px',
    height: h + 'px',
    transform: `translate(${tx}px, ${ty}px) scale(${calScaleX.value * fx}, ${calScaleY.value * fy})`,
    transformOrigin: 'top left'
  }
})

const previewWrapperStyle = computed(() => {
  const w = tlEffectiveWMm.value * BASE_PX_PER_MM * calScaleX.value
  const h = tlEffectiveHMm.value * BASE_PX_PER_MM * calScaleY.value
  return { width: w + 'px', height: h + 'px' }
})

const formRules = {
  模板名称: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  模板类型: [{ required: true, message: '请选择模板类型', trigger: 'change' }]
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
  Object.assign(layoutConfig, { ...defaultLayoutConfig, nameAutoAdjust: true, yangshangAutoAdjust: true })
  Object.assign(contentTemplate, { namesTitle: '佛光注照' })
  displayItems.value = ['seat', 'fahui_name']
}

const handleTypeChange = (val) => {
  if (val === '延生牌位') {
    contentTemplate.namesTitle = '佛光注照'
    displayItems.value = ['seat', 'fahui_name']
  } else if (val === '往生牌位') {
    contentTemplate.namesTitle = '佛光接引'
    displayItems.value = ['seat', 'fahui_name', 'yangshang']
  } else if (val === '佛事牌子') {
    contentTemplate.namesTitle = '佛力超度'
    displayItems.value = ['shizhu_name']
  }
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
  if (row.模板类型 === '往生牌位' && !displayItems.value.includes('yangshang')) {
    displayItems.value = [...displayItems.value, 'yangshang']
  }
}

const initSampleData = () => {
  const base = defaultSampleData()
  if (props.initialSampleData) {
    Object.assign(sampleData, base, props.initialSampleData)
  } else {
    Object.assign(sampleData, base)
  }
}

const initEditor = () => {
  resetForm()
  initSampleData()
  if (props.template) {
    Object.assign(formData, {
      id: props.copyMode ? null : props.template.id,
      模板名称: props.copyMode ? (props.template.模板名称 + ' (副本)') : props.template.模板名称,
      模板类型: props.template.模板类型,
      牌位类型: props.template.牌位类型,
      是否启用: props.copyMode ? 1 : props.template.是否启用,
      备注: props.template.备注
    })
    loadConfig(props.template)
  }
}

watch(() => props.visible, (val) => {
  if (val) initEditor()
}, { immediate: true })

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

const scanning = ref(false)
const scannerVisible = ref(false)
const scannerDevices = ref([])
const scannerDeviceId = ref('')
const scannerListLoading = ref(false)
const scanResolution = ref(200)
const scanColorMode = ref(1)
const scanAutoRotate = ref(true)

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
        emit('saved')
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error('操作失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}
</script>

<style scoped>
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
.zoom-value { font-size: 12px; color: #409eff; min-width: 36px; text-align: center; }
.preview-info { color: #606266; font-size: 13px; }
.preview-container { flex: 1; background: #e8e8e8; border-radius: 4px; padding: 15px; overflow: auto; }
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
.editable-cell { outline: none; border-radius: 2px; transition: background 0.15s; min-width: 1em; min-height: 1em; }
.editable-cell:hover { background: rgba(64, 158, 255, 0.12); box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.3); }
.editable-cell:focus { background: rgba(64, 158, 255, 0.18); box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.6); }
.add-name-btn { white-space: nowrap; user-select: none; position: absolute; left: 0; top: 0; }
.add-name-btn:hover { color: #409eff !important; border-color: #409eff !important; }
</style>
