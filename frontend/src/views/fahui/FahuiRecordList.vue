<template>
  <div class="fahui-record-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>法会登记</span>
          <div>
            <el-button type="success" @click="openBatchPasteDialog">批量粘贴录入</el-button>
            <el-button type="primary" @click="handleAdd">新增登记</el-button>
          </div>
        </div>
      </template>
      
      <div class="search-bar">
        <el-select v-model="searchForm.fahui_name" placeholder="法会名称" clearable style="width: 150px" @change="handleSearch">
          <el-option v-for="item in fahuiList" :key="item.id" :label="item.法会名称" :value="item.法会名称" />
        </el-select>
        <el-input v-model="searchForm.shizhu_name" placeholder="施主姓名" clearable style="width: 150px; margin-left: 10px" @keyup.enter="handleSearch" />
        <el-select v-model="searchForm.paiwei_type" placeholder="牌位类型" clearable style="width: 120px; margin-left: 10px" @change="handleSearch">
          <el-option label="大牌" value="大牌" />
          <el-option label="中牌" value="中牌" />
          <el-option label="小牌" value="小牌" />
        </el-select>
        <el-select v-model="searchForm.yanwang" placeholder="类型" clearable style="width: 120px; margin-left: 10px" @change="handleSearch">
          <el-option label="延生" value="0" />
          <el-option label="往生" value="1" />
        </el-select>
        <el-select v-model="searchForm.prt" placeholder="打印状态" clearable style="width: 120px; margin-left: 10px" @change="handleSearch">
          <el-option label="未打印" value="0" />
          <el-option label="已打印" value="1" />
        </el-select>
        <el-button type="primary" style="margin-left: 10px" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
        <el-button type="danger" :disabled="selectedRows.length === 0" style="margin-left: 10px" @click="handleBatchDelete">
          批量删除<template v-if="selectedRows.length > 0"> ({{ selectedRows.length }})</template>
        </el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe max-height="500" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="座次" label="座次" width="70" />
        <el-table-column prop="施主编号" label="施主编号" width="120" />
        <el-table-column prop="施主姓名" label="施主姓名" width="100" />
        <el-table-column prop="fahui_name" label="法会名称" width="120" />
        <el-table-column prop="paiwei_type" label="牌位类型" width="80" />
        <el-table-column prop="amount" label="金额" width="100">
          <template #default="{ row }">
            {{ row.amount?.toFixed(2) }} 元
          </template>
        </el-table-column>
        <el-table-column prop="yanwang" label="类型" width="70">
          <template #default="{ row }">
            <el-tag :type="row.yanwang === 0 ? 'success' : 'danger'" size="small">
              {{ row.yanwang === 0 ? '延生' : '往生' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="xm1" label="姓名1" width="80">
          <template #default="{ row }">
            {{ row.xm1 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="xm2" label="姓名2" width="80">
          <template #default="{ row }">
            {{ row.xm2 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="djdate" label="登记日期" width="100" />
        <el-table-column prop="经办人" label="经办人" width="80">
          <template #default="{ row }">
            {{ row.经办人 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="prt" label="打印状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.prt === 1 ? 'success' : 'info'" size="small">
              {{ row.prt === 1 ? '已打印' : '未打印' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.prt === 0" type="success" link @click="handlePrint(row)">打印</el-button>
            <el-button v-if="row.prt === 1" type="warning" link @click="handleReprint(row)">重新打印</el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
      
      <div class="statistics">
        <span>共 {{ total }} 条记录</span>
        <span style="margin-left: 20px">金额合计: {{ totalAmount.toFixed(2) }} 元</span>
      </div>
    </el-card>
    
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑法会登记' : '新增法会登记'"
      width="700px"
      destroy-on-close
    >
      <div class="sticky-info">
        <span v-if="formData.fahui_name" class="info-tag">
          <el-tag type="primary" size="large">{{ formData.fahui_name }}</el-tag>
        </span>
        <span v-if="selectedShizhuName" class="info-tag">
          <el-tag type="success" size="large">{{ selectedShizhuName }}</el-tag>
        </span>
        <el-tag v-if="formData.yanwang === '0' || formData.yanwang === '1'" :type="formData.yanwang === '0' ? 'warning' : 'danger'" size="large">
          {{ formData.yanwang === '0' ? '延生' : '往生' }}
        </el-tag>
        <el-button type="info" size="small" style="margin-left: auto;" @click="openPasteDialog">从Excel粘贴</el-button>
      </div>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="法会名称" prop="fahui_name">
              <div style="display: flex; gap: 8px;">
                <template v-if="!fahuiSelecting">
                  <el-input
                    :model-value="displayFahuiLabel"
                    readonly
                    placeholder="请选择法会"
                    style="flex: 1"
                  />
                  <el-button type="primary" @click="openFahuiSelect">选择</el-button>
                </template>
                <template v-else>
                  <el-select
                    ref="fahuiSelectRef"
                    v-model="tempFahuiName"
                    filterable
                    placeholder="请选择法会"
                    style="flex: 1"
                    @change="confirmFahuiSelect"
                  >
                    <el-option v-for="item in fahuiList" :key="item.id" :label="item.法会名称" :value="item.法会名称" />
                  </el-select>
                  <el-button @click="cancelFahuiSelect">取消</el-button>
                </template>
                <el-button type="primary" @click="handleOpenAddFahui">新增</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型" prop="yanwang">
              <el-radio-group v-model="formData.yanwang" @change="handleYanwangChange">
                <el-radio value="0">延生</el-radio>
                <el-radio value="1">往生</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="施主" prop="fahui_user_id">
              <div style="display: flex; gap: 8px;">
                <template v-if="!shizhuSelecting">
                  <el-input
                    :model-value="displayShizhuLabel"
                    readonly
                    placeholder="请选择施主"
                    style="flex: 1"
                  />
                  <el-button type="primary" @click="openShizhuSelect">选择</el-button>
                </template>
                <template v-else>
                  <el-select
                    ref="shizhuSelectRef"
                    v-model="tempShizhuId"
                    filterable
                    remote
                    :remote-method="handleShizhuSearch"
                    :loading="shizhuLoading"
                    placeholder="输入姓名/编号搜索"
                    style="flex: 1"
                    @change="confirmShizhuSelect"
                  >
                    <el-option
                      v-for="item in shizhuList"
                      :key="item.id"
                      :label="item.施主姓名 ? `${item.施主姓名} (${item.施主编号})` : item.施主编号"
                      :value="item.id"
                    />
                  </el-select>
                  <el-button @click="cancelShizhuSelect">取消</el-button>
                </template>
                <el-button type="primary" @click="handleOpenAddShizhu">新增</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="牌位类型" prop="paiwei_type">
              <el-select v-model="formData.paiwei_type" style="width: 100%">
                <el-option label="大牌" value="大牌" />
                <el-option label="中牌" value="中牌" />
                <el-option label="小牌" value="小牌" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <template v-if="formData.yanwang === '0'">
          <el-divider content-position="left">佛光注照</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光注照1">
                <el-input v-model="formData.xm1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光注照2">
                <el-input v-model="formData.xm2" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光注照3">
                <el-input v-model="formData.xm3" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光注照4">
                <el-input v-model="formData.xm4" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="佛光注照5">
            <el-input v-model="formData.xm5" />
          </el-form-item>
        </template>

        <template v-else>
          <el-divider content-position="left">佛光接引</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光接引1">
                <el-input v-model="formData.xm1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光接引2">
                <el-input v-model="formData.xm2" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光接引3">
                <el-input v-model="formData.xm3" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光接引4">
                <el-input v-model="formData.xm4" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-divider content-position="left">阳上</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="阳上1">
                <el-input v-model="formData.xm5" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="阳上2">
                <el-input v-model="formData.xm6" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="阳上3">
                <el-input v-model="formData.xm7" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="阳上4">
                <el-input v-model="formData.xm8" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="阳上5">
                <el-input v-model="formData.xm9" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="阳上6">
                <el-input v-model="formData.xm10" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        
        <el-divider content-position="left">登记信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="座次">
              <el-input v-model="formData.座次" :disabled="true" :placeholder="isEdit ? '' : '保存后自动生成'" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="金额" prop="amount">
              <el-input-number v-model="formData.amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="登记日期">
              <el-date-picker
                v-model="formData.djdate"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="备注">
          <el-input v-model="formData.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="pasteDialogVisible"
      title="从Excel粘贴数据"
      width="600px"
      destroy-on-close
    >
      <el-alert
        type="info"
        :closable="false"
        style="margin-bottom: 12px;"
      >
        <div>请从Excel中复制一行数据（包含类型、牌位、金额、姓名等列），粘贴到下方文本框中。</div>
        <div style="margin-top:4px; color:#909399; font-size:12px;">支持的列：类型 | 牌位 | 金额 | 每月放生姓名 | 姓名2 | 姓名3 | 姓名4 | 姓名5</div>
      </el-alert>
      <el-input
        v-model="pasteText"
        type="textarea"
        :rows="5"
        placeholder="在此处粘贴从Excel复制的行数据..."
      />
      <template #footer>
        <el-button @click="pasteDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePasteExcel">解析并填充</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="batchPasteDialogVisible"
      title="批量粘贴录入"
      width="900px"
      destroy-on-close
    >
      <el-form :inline="true" style="margin-bottom: 12px;">
        <el-form-item label="法会名称" required>
          <el-select v-model="batchPasteForm.fahui_name" filterable placeholder="选择法会" style="width: 200px" @change="handleBatchFahuiSelect">
            <el-option v-for="item in fahuiList" :key="item.id" :label="item.法会名称" :value="item.法会名称" />
          </el-select>
        </el-form-item>
        <el-form-item label="登记日期">
          <el-date-picker v-model="batchPasteForm.djdate" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 160px" />
        </el-form-item>
      </el-form>

      <el-alert type="info" :closable="false" style="margin-bottom: 12px;">
        <div>从Excel复制多行数据（每行一条记录），粘贴到下方文本框。点击"解析"后可预览数据，确认后批量创建。</div>
        <div style="margin-top:4px; color:#909399; font-size:12px;">Excel列顺序：类型 | 牌位 | 金额 | 每月放生姓名 | 姓名2 | 姓名3 | 姓名4 | 姓名5</div>
      </el-alert>

      <el-input
        v-model="batchPasteText"
        type="textarea"
        :rows="8"
        placeholder="在此处粘贴从Excel复制的多行数据..."
        style="margin-bottom: 12px;"
      />

      <div style="margin-bottom: 12px;">
        <el-button type="primary" @click="parseBatchPaste" :disabled="!batchPasteText.trim()">解析数据</el-button>
        <el-button @click="batchPastePreview = []; batchPasteText = ''">清空</el-button>
      </div>

      <el-table v-if="batchPastePreview.length > 0" :data="batchPastePreview" border max-height="300" stripe size="small">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="yanwangLabel" label="类型" width="70" />
        <el-table-column prop="paiwei_type" label="牌位" width="70" />
        <el-table-column prop="amount" label="金额" width="80" />
        <el-table-column prop="xm1" label="姓名1" width="100" show-overflow-tooltip />
        <el-table-column prop="xm2" label="姓名2" width="100" show-overflow-tooltip />
        <el-table-column prop="xm3" label="姓名3" width="100" show-overflow-tooltip />
        <el-table-column prop="xm4" label="姓名4" width="100" show-overflow-tooltip />
        <el-table-column prop="xm5" label="姓名5" width="100" show-overflow-tooltip />
      </el-table>

      <template #footer>
        <el-button @click="batchPasteDialogVisible = false">取消</el-button>
        <el-button type="success" @click="handleBatchSubmit" :loading="batchSubmitLoading" :disabled="batchPastePreview.length === 0 || !batchPasteForm.fahui_name">
          批量创建 ({{ batchPastePreview.length }} 条)
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="addFahuiDialogVisible"
      title="新增法会"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="addFahuiFormRef"
        :model="addFahuiFormData"
        :rules="addFahuiFormRules"
        label-width="100px"
      >
        <el-form-item label="法会名称" prop="法会名称">
          <el-input v-model="addFahuiFormData.法会名称" placeholder="请输入法会名称" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="addFahuiFormData.开始日期"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="addFahuiFormData.截止日期"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="功德金大">
              <el-input v-model="addFahuiFormData.功德金大" placeholder="金额" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="功德金中">
              <el-input v-model="addFahuiFormData.功德金中" placeholder="金额" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="功德金小">
              <el-input v-model="addFahuiFormData.功德金小" placeholder="金额" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="addFahuiFormData.备注" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addFahuiDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitAddFahui" :loading="addFahuiLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="addShizhuDialogVisible"
      title="新增施主"
      width="700px"
      destroy-on-close
    >
      <el-form
        ref="addShizhuFormRef"
        :model="addShizhuFormData"
        :rules="addShizhuFormRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="施主编号" prop="施主编号">
              <el-input v-model="addShizhuFormData.施主编号" placeholder="自动生成" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="施主姓名" prop="施主姓名">
              <el-input v-model="addShizhuFormData.施主姓名" placeholder="请输入施主姓名" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="addShizhuFormData.电话" placeholder="请输入电话" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="地址">
          <el-input v-model="addShizhuFormData.地址" placeholder="请输入地址" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="功德主">
              <el-switch
                v-model="addShizhuFormData.功德主"
                :active-value="1"
                :inactive-value="0"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">佛光接引</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光接引一">
              <el-input v-model="addShizhuFormData.佛光接引一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光接引二">
              <el-input v-model="addShizhuFormData.佛光接引二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光接引三">
              <el-input v-model="addShizhuFormData.佛光接引三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光接引四">
              <el-input v-model="addShizhuFormData.佛光接引四" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">阳上</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上一">
              <el-input v-model="addShizhuFormData.阳上一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上二">
              <el-input v-model="addShizhuFormData.阳上二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上三">
              <el-input v-model="addShizhuFormData.阳上三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上四">
              <el-input v-model="addShizhuFormData.阳上四" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上五">
              <el-input v-model="addShizhuFormData.阳上五" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上六">
              <el-input v-model="addShizhuFormData.阳上六" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">佛光注照</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光注照一">
              <el-input v-model="addShizhuFormData.佛光注照一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光注照二">
              <el-input v-model="addShizhuFormData.佛光注照二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光注照三">
              <el-input v-model="addShizhuFormData.佛光注照三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光注照四">
              <el-input v-model="addShizhuFormData.佛光注照四" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="备注">
          <el-input v-model="addShizhuFormData.备注" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addShizhuDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitAddShizhu" :loading="addShizhuLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fahuiRecordApi } from '@/api/fahuiRecords'
import { fahuiUserApi } from '@/api/fahuiUsers'
import { fahuiInfoApi } from '@/api/fahuiInfo'
import { printerTemplateApi } from '@/api/printerTemplates'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const fahuiList = ref([])
const shizhuList = ref([])
const shizhuLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const fahuiSelectRef = ref(null)
const shizhuSelectRef = ref(null)
const pasteDialogVisible = ref(false)
const pasteText = ref('')
const batchPasteDialogVisible = ref(false)
const batchPasteText = ref('')
const batchPastePreview = ref([])
const batchSubmitLoading = ref(false)
const batchPasteForm = reactive({
  fahui_id: null,
  fahui_name: '',
  djdate: new Date().toISOString().split('T')[0]
})
const selectedRows = ref([])
const fahuiSelecting = ref(false)
const tempFahuiName = ref('')
const selectedFahuiInfo = ref(null)
const shizhuSelecting = ref(false)
const tempShizhuId = ref(null)
const selectedShizhuInfo = ref(null)

const displayFahuiLabel = computed(() => {
  if (!formData.fahui_name) return ''
  if (selectedFahuiInfo.value && selectedFahuiInfo.value.法会名称 === formData.fahui_name) {
    return selectedFahuiInfo.value.法会名称
  }
  const fahui = fahuiList.value.find(item => item.法会名称 === formData.fahui_name)
  return fahui ? fahui.法会名称 : ''
})

const displayShizhuLabel = computed(() => {
  if (!formData.fahui_user_id) return ''
  if (selectedShizhuInfo.value && selectedShizhuInfo.value.id == formData.fahui_user_id) {
    return selectedShizhuInfo.value.施主姓名
      ? `${selectedShizhuInfo.value.施主姓名} (${selectedShizhuInfo.value.施主编号})`
      : selectedShizhuInfo.value.施主编号
  }
  const shizhu = shizhuList.value.find(item => item.id == formData.fahui_user_id)
  return shizhu ? (shizhu.施主姓名 ? `${shizhu.施主姓名} (${shizhu.施主编号})` : shizhu.施主编号) : ''
})

const selectedShizhuName = computed(() => {
  return displayShizhuLabel.value
})

const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalAmount = ref(0)

const searchForm = reactive({
  fahui_name: '',
  shizhu_name: '',
  paiwei_type: '',
  yanwang: '',
  prt: ''
})

const formData = reactive({
  id: null,
  fahui_id: '',
  fahui_name: '',
  fahui_user_id: null,
  座次: '',
  xm1: '',
  xm2: '',
  xm3: '',
  xm4: '',
  xm5: '',
  xm6: '',
  xm7: '',
  xm8: '',
  xm9: '',
  xm10: '',
  paiwei_type: '中牌',
  yanwang: '0',
  amount: 0,
  djdate: '',
  prt: '0',
  remarks: ''
})

const formRules = {
  fahui_name: [{ required: true, message: '请选择法会', trigger: 'change' }],
  fahui_user_id: [{ required: true, message: '请选择施主', trigger: 'change' }],
  paiwei_type: [{ required: true, message: '请选择牌位类型', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (searchForm.fahui_name) params.fahui_name = searchForm.fahui_name
    if (searchForm.shizhu_name) params.shizhu_name = searchForm.shizhu_name
    if (searchForm.paiwei_type) params.paiwei_type = searchForm.paiwei_type
    if (searchForm.yanwang !== '' && searchForm.yanwang !== null) params.yanwang = searchForm.yanwang
    if (searchForm.prt !== '' && searchForm.prt !== null) params.prt = searchForm.prt

    const res = await fahuiRecordApi.queryByFahui(params)
    tableData.value = res.records || []
    total.value = res.total || 0
    totalAmount.value = res.total_amount || 0
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchFahuiList = async () => {
  try {
    const res = await fahuiInfoApi.getList()
    fahuiList.value = res
  } catch (error) {
    console.error('获取法会列表失败:', error)
  }
}

const fetchShizhuList = async (keyword = '') => {
  shizhuLoading.value = true
  try {
    const res = await fahuiUserApi.getList(keyword || undefined, 500)
    shizhuList.value = res
  } catch (error) {
    console.error('获取施主列表失败:', error)
  } finally {
    shizhuLoading.value = false
  }
}

const handleShizhuSearch = (query) => {
  fetchShizhuList(query)
}

const openShizhuSelect = async () => {
  shizhuSelecting.value = true
  tempShizhuId.value = formData.fahui_user_id
  await fetchShizhuList('')
  await nextTick()
  // 如果当前施主不在列表中，手动加入以便下拉能默认选中
  if (tempShizhuId.value && !shizhuList.value.find(item => item.id == tempShizhuId.value) && selectedShizhuInfo.value) {
    shizhuList.value.unshift({ ...selectedShizhuInfo.value })
  }
  shizhuSelectRef.value?.focus?.()
}

const confirmShizhuSelect = (val) => {
  formData.fahui_user_id = val
  shizhuSelecting.value = false
  tempShizhuId.value = null
  const shizhu = shizhuList.value.find(item => item.id == val)
  if (shizhu) {
    selectedShizhuInfo.value = {
      id: shizhu.id,
      施主编号: shizhu.施主编号 || '',
      施主姓名: shizhu.施主姓名 || ''
    }
    fillNamesFromShizhu(shizhu)
  } else {
    selectedShizhuInfo.value = null
  }
}

const cancelShizhuSelect = () => {
  shizhuSelecting.value = false
  tempShizhuId.value = null
}

const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    fahui_name: '',
    shizhu_name: '',
    paiwei_type: '',
    yanwang: '',
    prt: ''
  })
  currentPage.value = 1
  fetchData()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}

const resetForm = () => {
  const today = new Date().toISOString().split('T')[0]
  Object.assign(formData, {
    id: null,
    fahui_id: '',
    fahui_name: '',
    fahui_user_id: null,
    座次: '',
    xm1: '',
    xm2: '',
    xm3: '',
    xm4: '',
    xm5: '',
    xm6: '',
    xm7: '',
    xm8: '',
    xm9: '',
    xm10: '',
    paiwei_type: '中牌',
    yanwang: '0',
    amount: 0,
    djdate: today,
    prt: '0',
    remarks: ''
  })
  fahuiSelecting.value = false
  tempFahuiName.value = ''
  selectedFahuiInfo.value = null
  shizhuSelecting.value = false
  tempShizhuId.value = null
  selectedShizhuInfo.value = null
}

const handleAdd = async () => {
  resetForm()
  isEdit.value = false
  if (fahuiList.value.length === 0) {
    await fetchFahuiList()
  }
  dialogVisible.value = true
  await nextTick()
}

const handleEdit = async (row) => {
  resetForm()
  isEdit.value = true
  if (fahuiList.value.length === 0) {
    await fetchFahuiList()
  }
  dialogVisible.value = true
  await nextTick()
  // 直接用行数据缓存当前法会/施主信息，避免依赖 select 回显
  if (row.fahui_name) {
    selectedFahuiInfo.value = {
      id: row.fahui_id,
      法会名称: row.fahui_name
    }
  }
  if (row.fahui_user_id) {
    selectedShizhuInfo.value = {
      id: row.fahui_user_id,
      施主编号: row.施主编号 || '',
      施主姓名: row.施主姓名 || ''
    }
  }
  Object.assign(formData, {
    id: row.id,
    fahui_id: row.fahui_id,
    fahui_name: row.fahui_name,
    fahui_user_id: row.fahui_user_id ? Number(row.fahui_user_id) : null,
    座次: row.座次,
    xm1: row.xm1,
    xm2: row.xm2,
    xm3: row.xm3,
    xm4: row.xm4,
    xm5: row.xm5,
    xm6: row.xm6,
    xm7: row.xm7,
    xm8: row.xm8,
    xm9: row.xm9,
    xm10: row.xm10,
    paiwei_type: row.paiwei_type,
    yanwang: String(row.yanwang),
    amount: row.amount,
    djdate: row.djdate,
    prt: String(row.prt),
    remarks: row.remarks
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该法会登记记录吗？', '提示', {
      type: 'warning'
    })
    await fahuiRecordApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedRows.value.length} 条记录吗？`, '提示', {
      type: 'warning'
    })
    const ids = selectedRows.value.map(row => row.id)
    for (const id of ids) {
      await fahuiRecordApi.delete(id)
    }
    ElMessage.success(`成功删除 ${ids.length} 条记录`)
    selectedRows.value = []
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

const handlePrint = async (row) => {
  try {
    const templateType = row.yanwang === 0 ? '延生牌位' : '往生牌位'
    const res = await printerTemplateApi.getList(templateType)
    const templates = res.filter(t => t.是否启用 === 1)
    
    if (templates.length === 0) {
      ElMessage.warning('没有可用的打印模板，请先在打印管理中创建模板')
      return
    }
    
    const defaultTemplate = templates.find(t => t.是否默认 === 1) || templates[0]
    
    const records = [{
      id: row.id,
      xm1: row.xm1,
      xm2: row.xm2,
      xm3: row.xm3,
      xm4: row.xm4,
      xm5: row.xm5,
      xm6: row.xm6,
      xm7: row.xm7,
      xm8: row.xm8,
      xm9: row.xm9,
      xm10: row.xm10,
      fahui_name: row.fahui_name,
      zuoweinum: row.座次,
      paiwei_type: row.paiwei_type
    }]
    
    const response = await printerTemplateApi.generatePdf({
      template_id: defaultTemplate.id,
      records: records
    })
    
    const blob = new Blob([response], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    
    await fahuiRecordApi.update(row.id, { prt: 1 })
    ElMessage.success('PDF已生成，请在浏览器中打印')
    fetchData()
  } catch (error) {
    console.error('打印失败:', error)
    ElMessage.error('打印失败')
  }
}

const handleReprint = async (row) => {
  try {
    await ElMessageBox.confirm('该排位已打印，确定要重新打印吗？', '重新打印确认', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    handlePrint(row)
  } catch {
    // cancelled
  }
}

const applyFahuiByName = (name) => {
  const fahui = fahuiList.value.find(item => item.法会名称 === name)
  if (fahui) {
    formData.fahui_id = fahui.id
  }
}

const openFahuiSelect = async () => {
  if (fahuiList.value.length === 0) {
    await fetchFahuiList()
  }
  fahuiSelecting.value = true
  tempFahuiName.value = formData.fahui_name || ''
  await nextTick()
  fahuiSelectRef.value?.focus?.()
}

const confirmFahuiSelect = (val) => {
  formData.fahui_name = val
  fahuiSelecting.value = false
  tempFahuiName.value = ''
  const fahui = fahuiList.value.find(item => item.法会名称 === val)
  if (fahui) {
    selectedFahuiInfo.value = {
      id: fahui.id,
      法会名称: fahui.法会名称
    }
    formData.fahui_id = fahui.id
  } else {
    selectedFahuiInfo.value = null
  }
}

const cancelFahuiSelect = () => {
  fahuiSelecting.value = false
  tempFahuiName.value = ''
}

const applyShizhuById = (id) => {
  if (!id) {
    formData.xm1 = ''
    formData.xm2 = ''
    formData.xm3 = ''
    formData.xm4 = ''
    formData.xm5 = ''
    formData.xm6 = ''
    formData.xm7 = ''
    formData.xm8 = ''
    formData.xm9 = ''
    formData.xm10 = ''
    return
  }
  const shizhu = shizhuList.value.find(item => item.id == id)
  if (shizhu) {
    fillNamesFromShizhu(shizhu)
  }
}

const handleYanwangChange = () => {
  formData.xm1 = ''
  formData.xm2 = ''
  formData.xm3 = ''
  formData.xm4 = ''
  formData.xm5 = ''
  formData.xm6 = ''
  formData.xm7 = ''
  formData.xm8 = ''
  formData.xm9 = ''
  formData.xm10 = ''
  if (formData.fahui_user_id) {
    applyShizhuById(formData.fahui_user_id)
  }
}

const fillNamesFromShizhu = (shizhu) => {
  if (formData.yanwang === '0') {
    formData.xm1 = shizhu.佛光注照一 || ''
    formData.xm2 = shizhu.佛光注照二 || ''
    formData.xm3 = shizhu.佛光注照三 || ''
    formData.xm4 = shizhu.佛光注照四 || ''
    formData.xm5 = ''
    formData.xm6 = ''
    formData.xm7 = ''
    formData.xm8 = ''
    formData.xm9 = ''
    formData.xm10 = ''
  } else {
    formData.xm1 = shizhu.佛光接引一 || ''
    formData.xm2 = shizhu.佛光接引二 || ''
    formData.xm3 = shizhu.佛光接引三 || ''
    formData.xm4 = shizhu.佛光接引四 || ''
    formData.xm5 = shizhu.阳上一 || ''
    formData.xm6 = shizhu.阳上二 || ''
    formData.xm7 = shizhu.阳上三 || ''
    formData.xm8 = shizhu.阳上四 || ''
    formData.xm9 = shizhu.阳上五 || ''
    formData.xm10 = shizhu.阳上六 || ''
  }
}

const openPasteDialog = () => {
  pasteText.value = ''
  pasteDialogVisible.value = true
}

const handlePasteExcel = () => {
  const raw = pasteText.value.trim()
  if (!raw) {
    ElMessage.warning('请粘贴数据')
    return
  }

  const lines = raw.split('\n')
  const firstLine = lines[0]
  const cols = firstLine.split('\t').map(c => c.trim())

  if (cols.length < 9) {
    ElMessage.warning('数据列数不足，请确保复制了完整的一行Excel数据（至少包含类型、牌位、金额、姓名等列）')
    return
  }

  // C列(索引2): 类型
  const type = cols[2]
  if (type === '延生') {
    formData.yanwang = '0'
  } else if (type === '往生') {
    formData.yanwang = '1'
  }

  // D列(索引3): 牌位
  const paiwei = cols[3]
  if (['大', '中', '小'].includes(paiwei)) {
    formData.paiwei_type = paiwei + '牌'
  } else if (['大牌', '中牌', '小牌'].includes(paiwei)) {
    formData.paiwei_type = paiwei
  }

  // F列(索引5): 金额
  const amountStr = cols[5]
  if (amountStr && amountStr !== '长期' && !isNaN(parseFloat(amountStr))) {
    formData.amount = parseFloat(amountStr)
  }

  // 清空姓名
  formData.xm1 = ''
  formData.xm2 = ''
  formData.xm3 = ''
  formData.xm4 = ''
  formData.xm5 = ''
  formData.xm6 = ''
  formData.xm7 = ''
  formData.xm8 = ''
  formData.xm9 = ''
  formData.xm10 = ''

  // I~M列(索引8~12): 姓名
  if (formData.yanwang === '0') {
    // 延生：佛光注照1~5
    formData.xm1 = cols[8] || ''
    formData.xm2 = cols[9] || ''
    formData.xm3 = cols[10] || ''
    formData.xm4 = cols[11] || ''
    formData.xm5 = cols[12] || ''
  } else {
    // 往生：佛光接引1~4，阳上1
    formData.xm1 = cols[8] || ''
    formData.xm2 = cols[9] || ''
    formData.xm3 = cols[10] || ''
    formData.xm4 = cols[11] || ''
    formData.xm5 = cols[12] || ''
  }

  pasteDialogVisible.value = false
  ElMessage.success('已根据Excel数据填充表单')
}

const openBatchPasteDialog = () => {
  batchPasteText.value = ''
  batchPastePreview.value = []
  batchPasteForm.fahui_id = null
  batchPasteForm.fahui_name = ''
  batchPasteForm.djdate = new Date().toISOString().split('T')[0]
  batchPasteDialogVisible.value = true
}

const handleBatchFahuiSelect = (val) => {
  const fahui = fahuiList.value.find(item => item.法会名称 === val)
  if (fahui) {
    batchPasteForm.fahui_id = fahui.id
  }
}

const parseBatchPaste = () => {
  const raw = batchPasteText.value.trim()
  if (!raw) {
    ElMessage.warning('请粘贴数据')
    return
  }

  const lines = raw.split('\n').filter(l => l.trim())
  const preview = []

  for (const line of lines) {
    const cols = line.split('\t').map(c => c.trim())

    if (cols.length < 4) {
      ElMessage.warning(`数据列数不足（需要至少4列：类型、牌位、金额、姓名），跳过该行`)
      continue
    }

    const type = cols[2] || '延生'
    const yanwang = type === '往生' ? 1 : 0
    const paiwei = cols[3] || '中'
    let paiweiType = '中牌'
    if (['大', '中', '小'].includes(paiwei)) {
      paiweiType = paiwei + '牌'
    } else if (['大牌', '中牌', '小牌'].includes(paiwei)) {
      paiweiType = paiwei
    }

    const amountStr = cols[5] || ''
    let amount = 0
    if (amountStr && amountStr !== '长期' && !isNaN(parseFloat(amountStr))) {
      amount = parseFloat(amountStr)
    }

    const row = {
      yanwang,
      yanwangLabel: type,
      paiwei_type: paiweiType,
      amount,
      xm1: cols[8] || '',
      xm2: cols[9] || '',
      xm3: cols[10] || '',
      xm4: cols[11] || '',
      xm5: cols[12] || '',
      xm: yanwang === 0 ? '佛光注照' : '佛光接引'
    }

    preview.push(row)
  }

  batchPastePreview.value = preview
  if (preview.length > 0) {
    ElMessage.success(`解析成功，共 ${preview.length} 条记录`)
  } else {
    ElMessage.warning('未解析到有效数据')
  }
}

const handleBatchSubmit = async () => {
  if (!batchPasteForm.fahui_name) {
    ElMessage.warning('请选择法会')
    return
  }
  if (batchPastePreview.value.length === 0) {
    ElMessage.warning('没有可提交的数据')
    return
  }

  batchSubmitLoading.value = true
  try {
    const payload = {
      fahui_id: batchPasteForm.fahui_id,
      fahui_name: batchPasteForm.fahui_name,
      djdate: batchPasteForm.djdate,
      records: batchPastePreview.value
    }
    const res = await fahuiRecordApi.batchCreate(payload)
    ElMessage.success(res.message || `成功创建 ${res.count} 条记录`)
    batchPasteDialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error('批量创建失败:', error)
    ElMessage.error(error.response?.data?.detail || '批量创建失败')
  } finally {
    batchSubmitLoading.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const submitData = {
          fahui_user_id: formData.fahui_user_id,
          fahui_id: formData.fahui_id || null,
          fahui_name: formData.fahui_name || null,
          xm1: formData.xm1 || null,
          xm2: formData.xm2 || null,
          xm3: formData.xm3 || null,
          xm4: formData.xm4 || null,
          xm5: formData.xm5 || null,
          xm6: formData.xm6 || null,
          xm7: formData.xm7 || null,
          xm8: formData.xm8 || null,
          xm9: formData.xm9 || null,
          xm10: formData.xm10 || null,
          xm: formData.yanwang === '0' ? '佛光注照' : '佛光接引',
          paiwei_type: formData.paiwei_type || null,
          yanwang: parseInt(formData.yanwang),
          amount: parseFloat(formData.amount) || 0,
          djdate: formData.djdate || null,
          prt: parseInt(formData.prt),
          remarks: formData.remarks || null
        }
        console.log('提交数据:', submitData)
        if (isEdit.value) {
          await fahuiRecordApi.update(formData.id, submitData)
          ElMessage.success('更新成功')
        } else {
          await fahuiRecordApi.create(submitData)
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

const addFahuiDialogVisible = ref(false)
const addFahuiLoading = ref(false)
const addFahuiFormRef = ref(null)
const addFahuiFormData = reactive({
  法会名称: '',
  开始日期: '',
  截止日期: '',
  功德金大: '',
  功德金中: '',
  功德金小: '',
  备注: ''
})

const addFahuiFormRules = {
  法会名称: [{ required: true, message: '请输入法会名称', trigger: 'blur' }]
}

const handleOpenAddFahui = () => {
  Object.assign(addFahuiFormData, {
    法会名称: '',
    开始日期: '',
    截止日期: '',
    功德金大: '',
    功德金中: '',
    功德金小: '',
    备注: ''
  })
  addFahuiDialogVisible.value = true
}

const handleSubmitAddFahui = async () => {
  if (!addFahuiFormRef.value) return
  
  await addFahuiFormRef.value.validate(async (valid) => {
    if (valid) {
      addFahuiLoading.value = true
      try {
        await fahuiInfoApi.create(addFahuiFormData)
        ElMessage.success('法会创建成功')
        addFahuiDialogVisible.value = false
        await fetchFahuiList()
        formData.fahui_name = addFahuiFormData.法会名称
        const fahui = fahuiList.value.find(item => item.法会名称 === addFahuiFormData.法会名称)
        if (fahui) {
          formData.fahui_id = fahui.id
        }
      } catch (error) {
        console.error('创建法会失败:', error)
        ElMessage.error('创建法会失败')
      } finally {
        addFahuiLoading.value = false
      }
    }
  })
}

const addShizhuDialogVisible = ref(false)
const addShizhuLoading = ref(false)
const addShizhuFormRef = ref(null)
const addShizhuFormData = reactive({
  施主编号: '',
  施主姓名: '',
  电话: '',
  地址: '',
  功德主: 1,
  佛光接引一: '',
  佛光接引二: '',
  佛光接引三: '',
  佛光接引四: '',
  阳上一: '',
  阳上二: '',
  阳上三: '',
  阳上四: '',
  阳上五: '',
  阳上六: '',
  佛光注照一: '',
  佛光注照二: '',
  佛光注照三: '',
  佛光注照四: '',
  备注: ''
})

const addShizhuFormRules = {
  施主姓名: [{ required: true, message: '请输入施主姓名', trigger: 'blur' }]
}

const handleOpenAddShizhu = async () => {
  Object.assign(addShizhuFormData, {
    施主编号: '',
    施主姓名: '',
    电话: '',
    地址: '',
    功德主: 1,
    佛光接引一: '',
    佛光接引二: '',
    佛光接引三: '',
    佛光接引四: '',
    阳上一: '',
    阳上二: '',
    阳上三: '',
    阳上四: '',
    阳上五: '',
    阳上六: '',
    佛光注照一: '',
    佛光注照二: '',
    佛光注照三: '',
    佛光注照四: '',
    备注: ''
  })
  try {
    const res = await fahuiUserApi.generateCode()
    addShizhuFormData.施主编号 = res.code
  } catch (error) {
    console.error('生成编号失败:', error)
  }
  addShizhuDialogVisible.value = true
}

const handleSubmitAddShizhu = async () => {
  if (!addShizhuFormRef.value) return
  
  await addShizhuFormRef.value.validate(async (valid) => {
    if (valid) {
      addShizhuLoading.value = true
      try {
        await fahuiUserApi.create(addShizhuFormData)
        ElMessage.success('施主创建成功')
        addShizhuDialogVisible.value = false
        await fetchShizhuList('')
        const newShizhu = shizhuList.value.find(item => item.施主编号 === addShizhuFormData.施主编号)
        if (newShizhu) {
          formData.fahui_user_id = newShizhu.id
          fillNamesFromShizhu(newShizhu)
        }
      } catch (error) {
        console.error('创建施主失败:', error)
        ElMessage.error('创建施主失败')
      } finally {
        addShizhuLoading.value = false
      }
    }
  })
}

onMounted(() => {
  fetchData()
  fetchFahuiList()
  fetchShizhuList()
})
</script>

<style scoped>
.fahui-record-list {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
}

.pagination-container {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.statistics {
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
}

.sticky-info {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #fff;
  padding: 10px 16px;
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-tag {
  display: inline-flex;
}
</style>
