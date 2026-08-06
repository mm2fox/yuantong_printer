<template>
  <div>
    <div class="filter-bar">
      <el-select v-model="fahuiName" clearable placeholder="选择法会" style="width: 200px" @change="handleFilterChange">
        <el-option v-for="item in fahuiList" :key="item.id" :label="item.法会名称" :value="item.法会名称" />
      </el-select>
      <el-select v-model="paiweiType" clearable placeholder="牌位类型" style="width: 120px; margin-left: 10px" @change="handleFilterChange">
        <el-option label="大牌" value="大牌" />
        <el-option label="中牌" value="中牌" />
        <el-option label="小牌" value="小牌" />
      </el-select>
      <el-select v-model="printStatus" clearable placeholder="打印状态" style="width: 120px; margin-left: 10px" @change="handleFilterChange">
        <el-option label="未打印" value="0" />
        <el-option label="已打印" value="1" />
      </el-select>
      <el-button type="primary" style="margin-left: 10px" @click="handlePrintSelected" :disabled="selectedRows.length === 0">
        批量打印 ({{ selectedRows.length }})
      </el-button>
      <el-button type="success" @click="handleMarkPrinted" :disabled="selectedRows.length === 0">
        标记已打印
      </el-button>
      <el-button type="warning" @click="handleMarkUnprinted" :disabled="selectedRows.length === 0">
        标记为未打印
      </el-button>
    </div>
    
    <el-table :data="tableData" v-loading="loading" stripe @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="fahui_name" label="法会名称" width="120" />
      <el-table-column prop="施主姓名" label="施主姓名" width="100" />
      <el-table-column prop="paiwei_type" label="牌位类型" width="80" />
      <el-table-column prop="amount" label="金额" width="100">
        <template #default="{ row }">{{ row.amount?.toFixed(2) }} 元</template>
      </el-table-column>
      <el-table-column prop="xm1" label="姓名1" width="80" />
      <el-table-column prop="xm2" label="姓名2" width="80" />
      <el-table-column prop="xm3" label="姓名3" width="80" />
      <el-table-column prop="xm4" label="姓名4" width="80" />
      <el-table-column prop="xm5" label="姓名5" width="80" />
      <el-table-column prop="prt" label="打印状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.prt === 1 ? 'success' : 'info'">{{ row.prt === 1 ? '已打印' : '未打印' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="handlePreview(row)">预览</el-button>
          <el-button type="success" link @click="handlePrint(row)">打印</el-button>
          <el-button type="warning" link @click="handleEdit(row)">修改</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="statistics">
      <span>共 {{ total }} 条记录</span>
      <span style="margin-left: 20px">金额合计: {{ totalAmount.toFixed(2) }} 元</span>
    </div>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
    
    <PrintPreviewDialog v-model:visible="previewVisible" :record="previewData" @printed="fetchData" />
    
    <el-dialog
      v-model="editVisible"
      title="编辑法会登记"
      width="700px"
      destroy-on-close
    >
      <div class="sticky-info">
        <span v-if="editForm.fahui_name" class="info-tag">
          <el-tag type="primary" size="large">{{ editForm.fahui_name }}</el-tag>
        </span>
        <span v-if="editSelectedShizhuName" class="info-tag">
          <el-tag type="success" size="large">{{ editSelectedShizhuName }}</el-tag>
        </span>
        <el-tag v-if="editForm.yanwang === '0' || editForm.yanwang === '1'" :type="editForm.yanwang === '0' ? 'warning' : 'danger'" size="large">
          {{ editForm.yanwang === '0' ? '延生' : '往生' }}
        </el-tag>
        <el-button type="info" size="small" style="margin-left: auto;" @click="openPasteDialog">从Excel粘贴</el-button>
      </div>

      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="法会名称" prop="fahui_name">
              <div style="display: flex; gap: 8px;">
                <el-select v-model="editForm.fahui_name" style="flex: 1" filterable @change="editHandleFahuiSelect">
                  <el-option v-for="item in fahuiList" :key="item.id" :label="item.法会名称" :value="item.法会名称" />
                </el-select>
                <el-button type="primary" @click="editHandleOpenAddFahui">新增</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型" prop="yanwang">
              <el-radio-group v-model="editForm.yanwang" @change="editHandleYanwangChange">
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
                <el-select
                  v-model="editForm.fahui_user_id"
                  filterable
                  remote
                  :remote-method="editHandleShizhuSearch"
                  :loading="editShizhuLoading"
                  placeholder="搜索选择施主"
                  style="flex: 1"
                  @change="editHandleShizhuSelect"
                >
                  <el-option
                    v-for="item in editShizhuList"
                    :key="item.id"
                    :label="`${item.施主姓名} (${item.施主编号})`"
                    :value="item.id"
                  />
                </el-select>
                <el-button type="primary" @click="editHandleOpenAddShizhu">新增</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="牌位类型" prop="paiwei_type">
              <el-select v-model="editForm.paiwei_type" style="width: 100%">
                <el-option label="大牌" value="大牌" />
                <el-option label="中牌" value="中牌" />
                <el-option label="小牌" value="小牌" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <template v-if="editForm.yanwang === '0'">
          <el-divider content-position="left">佛光注照</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光注照1">
                <el-input v-model="editForm.xm1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光注照2">
                <el-input v-model="editForm.xm2" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光注照3">
                <el-input v-model="editForm.xm3" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光注照4">
                <el-input v-model="editForm.xm4" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="佛光注照5">
            <el-input v-model="editForm.xm5" />
          </el-form-item>
        </template>

        <template v-else>
          <el-divider content-position="left">佛光接引</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光接引1">
                <el-input v-model="editForm.xm1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光接引2">
                <el-input v-model="editForm.xm2" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光接引3">
                <el-input v-model="editForm.xm3" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光接引4">
                <el-input v-model="editForm.xm4" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-divider content-position="left">阳上</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="阳上1">
                <el-input v-model="editForm.xm5" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="阳上2">
                <el-input v-model="editForm.xm6" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="阳上3">
                <el-input v-model="editForm.xm7" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="阳上4">
                <el-input v-model="editForm.xm8" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="阳上5">
                <el-input v-model="editForm.xm9" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="阳上6">
                <el-input v-model="editForm.xm10" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <el-divider content-position="left">登记信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="座次">
              <el-input v-model="editForm.座次" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="金额" prop="amount">
              <el-input-number v-model="editForm.amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="登记日期">
              <el-date-picker v-model="editForm.djdate" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="editForm.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit" :loading="editLoading">保存</el-button>
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
      v-model="editAddFahuiDialogVisible"
      title="新增法会"
      width="500px"
      destroy-on-close
    >
      <el-form ref="editAddFahuiFormRef" :model="editAddFahuiFormData" :rules="editAddFahuiFormRules" label-width="100px">
        <el-form-item label="法会名称" prop="法会名称">
          <el-input v-model="editAddFahuiFormData.法会名称" placeholder="请输入法会名称" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="editAddFahuiFormData.开始日期" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="editAddFahuiFormData.截止日期" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="功德金大">
              <el-input v-model="editAddFahuiFormData.功德金大" placeholder="金额" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="功德金中">
              <el-input v-model="editAddFahuiFormData.功德金中" placeholder="金额" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="功德金小">
              <el-input v-model="editAddFahuiFormData.功德金小" placeholder="金额" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="editAddFahuiFormData.备注" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editAddFahuiDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="editHandleSubmitAddFahui" :loading="editAddFahuiLoading">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="editAddShizhuDialogVisible"
      title="新增施主"
      width="700px"
      destroy-on-close
    >
      <el-form ref="editAddShizhuFormRef" :model="editAddShizhuFormData" :rules="editAddShizhuFormRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="施主编号" prop="施主编号">
              <el-input v-model="editAddShizhuFormData.施主编号" placeholder="自动生成" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="施主姓名" prop="施主姓名">
              <el-input v-model="editAddShizhuFormData.施主姓名" placeholder="请输入施主姓名" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="editAddShizhuFormData.电话" placeholder="请输入电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="地址">
          <el-input v-model="editAddShizhuFormData.地址" placeholder="请输入地址" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="功德主">
              <el-switch v-model="editAddShizhuFormData.功德主" :active-value="1" :inactive-value="0" active-text="是" inactive-text="否" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">佛光接引</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光接引一">
              <el-input v-model="editAddShizhuFormData.佛光接引一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光接引二">
              <el-input v-model="editAddShizhuFormData.佛光接引二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光接引三">
              <el-input v-model="editAddShizhuFormData.佛光接引三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光接引四">
              <el-input v-model="editAddShizhuFormData.佛光接引四" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">阳上</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上一">
              <el-input v-model="editAddShizhuFormData.阳上一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上二">
              <el-input v-model="editAddShizhuFormData.阳上二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上三">
              <el-input v-model="editAddShizhuFormData.阳上三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上四">
              <el-input v-model="editAddShizhuFormData.阳上四" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上五">
              <el-input v-model="editAddShizhuFormData.阳上五" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上六">
              <el-input v-model="editAddShizhuFormData.阳上六" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">佛光注照</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光注照一">
              <el-input v-model="editAddShizhuFormData.佛光注照一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光注照二">
              <el-input v-model="editAddShizhuFormData.佛光注照二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光注照三">
              <el-input v-model="editAddShizhuFormData.佛光注照三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光注照四">
              <el-input v-model="editAddShizhuFormData.佛光注照四" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="editAddShizhuFormData.备注" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editAddShizhuDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="editHandleSubmitAddShizhu" :loading="editAddShizhuLoading">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="batchPrintVisible" title="批量打印" width="500px">
      <div style="margin-bottom: 20px;">
        <span>已选择 <strong>{{ selectedRows.length }}</strong> 条记录</span>
      </div>
      <div style="margin-bottom: 15px;">
        <span style="margin-right: 10px;">打印模板:</span>
        <el-select v-model="selectedTemplateId" placeholder="选择打印模板" style="width: 300px">
          <el-option v-for="item in templateList" :key="item.id" :label="item.模板名称" :value="item.id" />
        </el-select>
      </div>
      <template #footer>
        <el-button @click="batchPrintVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchPrint" :disabled="!selectedTemplateId" :loading="batchPrintLoading">确认打印</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fahuiRecordApi } from '@/api/fahuiRecords'
import { fahuiUserApi } from '@/api/fahuiUsers'
import { fahuiInfoApi } from '@/api/fahuiInfo'
import { printerTemplateApi } from '@/api/printerTemplates'
import PrintPreviewDialog from '@/components/PrintPreviewDialog.vue'

const props = defineProps({
  type: {
    type: Number,
    default: 0
  }
})

const loading = ref(false)
const tableData = ref([])
const fahuiList = ref([])
const templateList = ref([])
const selectedTemplateId = ref(null)

const fahuiName = ref('')
const paiweiType = ref('')
const printStatus = ref('0')
const selectedRows = ref([])
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)
const previewVisible = ref(false)
const previewData = ref({})
const batchPrintVisible = ref(false)
const batchPrintLoading = ref(false)
const silentPrintLoading = ref(false)
const editVisible = ref(false)
const editLoading = ref(false)
const editFormRef = ref(null)
const pasteDialogVisible = ref(false)
const pasteText = ref('')
const editShizhuList = ref([])
const editShizhuLoading = ref(false)
const editSelectedShizhuName = computed(() => {
  if (!editForm.value.fahui_user_id) return ''
  const shizhu = editShizhuList.value.find(item => item.id === editForm.value.fahui_user_id)
  return shizhu ? `${shizhu.施主姓名} (${shizhu.施主编号})` : ''
})
const editForm = ref({
  id: null,
  fahui_id: '',
  fahui_name: '',
  fahui_user_id: null,
  座次: '',
  yanwang: '0',
  paiwei_type: '中牌',
  amount: 0,
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
  djdate: '',
  prt: '0',
  remarks: ''
})
const editRules = {
  fahui_name: [{ required: true, message: '请选择法会', trigger: 'change' }],
  paiwei_type: [{ required: true, message: '请选择牌位类型', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }]
}
const editAddFahuiDialogVisible = ref(false)
const editAddFahuiLoading = ref(false)
const editAddFahuiFormRef = ref(null)
const editAddFahuiFormData = reactive({
  法会名称: '',
  开始日期: '',
  截止日期: '',
  功德金大: '',
  功德金中: '',
  功德金小: '',
  备注: ''
})
const editAddFahuiFormRules = {
  法会名称: [{ required: true, message: '请输入法会名称', trigger: 'blur' }]
}
const editAddShizhuDialogVisible = ref(false)
const editAddShizhuLoading = ref(false)
const editAddShizhuFormRef = ref(null)
const editAddShizhuFormData = reactive({
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
const editAddShizhuFormRules = {}






































const totalAmount = computed(() => {
  return tableData.value.reduce((sum, row) => sum + (row.amount || 0), 0)
})

const fetchTemplateList = async () => {
  try {
    const templateType = props.type === 0 ? '延生牌位' : '往生牌位'
    const res = await printerTemplateApi.getList(templateType)
    templateList.value = res.filter(t => t.是否启用 === 1)
    if (templateList.value.length > 0 && !selectedTemplateId.value) {
      const defaultTemplate = templateList.value.find(t => t.是否默认 === 1)
      selectedTemplateId.value = defaultTemplate ? defaultTemplate.id : templateList.value[0].id
    }
  } catch (error) {
    console.error('获取模板列表失败:', error)
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



const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      yanwang: props.type,
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (fahuiName.value) params.fahui_name = fahuiName.value
    if (paiweiType.value) params.paiwei_type = paiweiType.value
    if (printStatus.value !== null && printStatus.value !== '') params.prt = parseInt(printStatus.value)
    const res = await fahuiRecordApi.queryByFahui(params)
    tableData.value = res.records || []
    total.value = res.total || 0
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const handlePageChange = (page) => {
  currentPage.value = page
  fetchData()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchData()
}

const editFetchShizhuList = async (keyword = '') => {
  editShizhuLoading.value = true
  try {
    const res = await fahuiUserApi.getList(keyword || undefined, 50)
    editShizhuList.value = res
  } catch (error) {
    console.error('获取施主列表失败:', error)
  } finally {
    editShizhuLoading.value = false
  }
}

const editHandleShizhuSearch = (query) => {
  editFetchShizhuList(query)
}

const editFillNamesFromShizhu = (shizhu) => {
  if (editForm.value.yanwang === '0') {
    editForm.value.xm1 = shizhu.佛光注照一 || ''
    editForm.value.xm2 = shizhu.佛光注照二 || ''
    editForm.value.xm3 = shizhu.佛光注照三 || ''
    editForm.value.xm4 = shizhu.佛光注照四 || ''
    editForm.value.xm5 = ''
    editForm.value.xm6 = ''
    editForm.value.xm7 = ''
    editForm.value.xm8 = ''
    editForm.value.xm9 = ''
    editForm.value.xm10 = ''
  } else {
    editForm.value.xm1 = shizhu.佛光接引一 || ''
    editForm.value.xm2 = shizhu.佛光接引二 || ''
    editForm.value.xm3 = shizhu.佛光接引三 || ''
    editForm.value.xm4 = shizhu.佛光接引四 || ''
    editForm.value.xm5 = shizhu.阳上一 || ''
    editForm.value.xm6 = shizhu.阳上二 || ''
    editForm.value.xm7 = shizhu.阳上三 || ''
    editForm.value.xm8 = shizhu.阳上四 || ''
    editForm.value.xm9 = shizhu.阳上五 || ''
    editForm.value.xm10 = shizhu.阳上六 || ''
  }
}

const editHandleFahuiSelect = (val) => {
  const fahui = fahuiList.value.find(item => item.法会名称 === val)
  if (fahui) {
    editForm.value.fahui_id = fahui.id
  }
}

const editHandleShizhuSelect = (val) => {
  if (!val) {
    editForm.value.xm1 = ''
    editForm.value.xm2 = ''
    editForm.value.xm3 = ''
    editForm.value.xm4 = ''
    editForm.value.xm5 = ''
    editForm.value.xm6 = ''
    editForm.value.xm7 = ''
    editForm.value.xm8 = ''
    editForm.value.xm9 = ''
    editForm.value.xm10 = ''
    return
  }
  const shizhu = editShizhuList.value.find(item => item.id === val)
  if (shizhu) {
    editFillNamesFromShizhu(shizhu)
  }
}

const editHandleYanwangChange = () => {
  editForm.value.xm1 = ''
  editForm.value.xm2 = ''
  editForm.value.xm3 = ''
  editForm.value.xm4 = ''
  editForm.value.xm5 = ''
  editForm.value.xm6 = ''
  editForm.value.xm7 = ''
  editForm.value.xm8 = ''
  editForm.value.xm9 = ''
  editForm.value.xm10 = ''
  if (editForm.value.fahui_user_id) {
    const shizhu = editShizhuList.value.find(item => item.id === editForm.value.fahui_user_id)
    if (shizhu) {
      editFillNamesFromShizhu(shizhu)
    }
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
    editForm.value.yanwang = '0'
  } else if (type === '往生') {
    editForm.value.yanwang = '1'
  }

  // D列(索引3): 牌位
  const paiwei = cols[3]
  if (['大', '中', '小'].includes(paiwei)) {
    editForm.value.paiwei_type = paiwei + '牌'
  } else if (['大牌', '中牌', '小牌'].includes(paiwei)) {
    editForm.value.paiwei_type = paiwei
  }

  // F列(索引5): 金额
  const amountStr = cols[5]
  if (amountStr && amountStr !== '长期' && !isNaN(parseFloat(amountStr))) {
    editForm.value.amount = parseFloat(amountStr)
  }

  // 清空姓名
  editForm.value.xm1 = ''
  editForm.value.xm2 = ''
  editForm.value.xm3 = ''
  editForm.value.xm4 = ''
  editForm.value.xm5 = ''
  editForm.value.xm6 = ''
  editForm.value.xm7 = ''
  editForm.value.xm8 = ''
  editForm.value.xm9 = ''
  editForm.value.xm10 = ''

  // I~M列(索引8~12): 姓名
  if (editForm.value.yanwang === '0') {
    // 延生：佛光注照1~5
    editForm.value.xm1 = cols[8] || ''
    editForm.value.xm2 = cols[9] || ''
    editForm.value.xm3 = cols[10] || ''
    editForm.value.xm4 = cols[11] || ''
    editForm.value.xm5 = cols[12] || ''
  } else {
    // 往生：佛光接引1~4，阳上1
    editForm.value.xm1 = cols[8] || ''
    editForm.value.xm2 = cols[9] || ''
    editForm.value.xm3 = cols[10] || ''
    editForm.value.xm4 = cols[11] || ''
    editForm.value.xm5 = cols[12] || ''
  }

  pasteDialogVisible.value = false
  ElMessage.success('已根据Excel数据填充表单')
}

const editHandleOpenAddFahui = () => {
  Object.assign(editAddFahuiFormData, {
    法会名称: '',
    开始日期: '',
    截止日期: '',
    功德金大: '',
    功德金中: '',
    功德金小: '',
    备注: ''
  })
  editAddFahuiDialogVisible.value = true
}

const editHandleSubmitAddFahui = async () => {
  if (!editAddFahuiFormRef.value) return
  await editAddFahuiFormRef.value.validate(async (valid) => {
    if (valid) {
      editAddFahuiLoading.value = true
      try {
        await fahuiInfoApi.create(editAddFahuiFormData)
        ElMessage.success('法会创建成功')
        editAddFahuiDialogVisible.value = false
        await fetchFahuiList()
        editForm.value.fahui_name = editAddFahuiFormData.法会名称
        const fahui = fahuiList.value.find(item => item.法会名称 === editAddFahuiFormData.法会名称)
        if (fahui) {
          editForm.value.fahui_id = fahui.id
        }
      } catch (error) {
        console.error('创建法会失败:', error)
        ElMessage.error('创建法会失败')
      } finally {
        editAddFahuiLoading.value = false
      }
    }
  })
}

const editHandleOpenAddShizhu = async () => {
  Object.assign(editAddShizhuFormData, {
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
    editAddShizhuFormData.施主编号 = res.code
  } catch (error) {
    console.error('生成编号失败:', error)
  }
  editAddShizhuDialogVisible.value = true
}

const editHandleSubmitAddShizhu = async () => {
  if (!editAddShizhuFormRef.value) return
  await editAddShizhuFormRef.value.validate(async (valid) => {
    if (valid) {
      editAddShizhuLoading.value = true
      try {
        await fahuiUserApi.create(editAddShizhuFormData)
        ElMessage.success('施主创建成功')
        editAddShizhuDialogVisible.value = false
        await editFetchShizhuList()
        const newShizhu = editShizhuList.value.find(item => item.施主编号 === editAddShizhuFormData.施主编号)
        if (newShizhu) {
          editForm.value.fahui_user_id = newShizhu.id
          editFillNamesFromShizhu(newShizhu)
        }
      } catch (error) {
        console.error('创建施主失败:', error)
        ElMessage.error('创建施主失败')
      } finally {
        editAddShizhuLoading.value = false
      }
    }
  })
}

const handleEdit = async (row) => {
  editForm.value = {
    id: row.id,
    fahui_id: row.fahui_id || '',
    fahui_name: row.fahui_name || '',
    fahui_user_id: row.fahui_user_id || null,
    座次: row.座次 || row.zuoweinum || '',
    yanwang: String(row.yanwang !== undefined ? row.yanwang : props.type),
    paiwei_type: row.paiwei_type || '中牌',
    amount: row.amount || 0,
    xm1: row.xm1 || '',
    xm2: row.xm2 || '',
    xm3: row.xm3 || '',
    xm4: row.xm4 || '',
    xm5: row.xm5 || '',
    xm6: row.xm6 || '',
    xm7: row.xm7 || '',
    xm8: row.xm8 || '',
    xm9: row.xm9 || '',
    xm10: row.xm10 || '',
    djdate: row.djdate || '',
    prt: String(row.prt !== undefined ? row.prt : '0'),
    remarks: row.remarks || ''
  }
  editVisible.value = true
  await editFetchShizhuList()
  if (row.fahui_user_id && !editShizhuList.value.find(item => item.id === row.fahui_user_id)) {
    editShizhuList.value.unshift({
      id: row.fahui_user_id,
      施主编号: row.施主编号 || '',
      施主姓名: row.施主姓名 || '',
      佛光注照一: row.xm1 || '',
      佛光注照二: row.xm2 || '',
      佛光注照三: row.xm3 || '',
      佛光注照四: row.xm4 || '',
      佛光接引一: row.xm1 || '',
      佛光接引二: row.xm2 || '',
      佛光接引三: row.xm3 || '',
      佛光接引四: row.xm4 || '',
      阳上一: row.xm5 || '',
      阳上二: row.xm6 || '',
      阳上三: row.xm7 || '',
      阳上四: row.xm8 || '',
      阳上五: row.xm9 || '',
      阳上六: row.xm10 || ''
    })
  }
}

const handleSaveEdit = async () => {
  if (!editFormRef.value) return
  try {
    await editFormRef.value.validate()
    editLoading.value = true
    const submitData = {
      fahui_user_id: editForm.value.fahui_user_id,
      fahui_id: editForm.value.fahui_id || null,
      fahui_name: editForm.value.fahui_name || null,
      xm1: editForm.value.xm1 || null,
      xm2: editForm.value.xm2 || null,
      xm3: editForm.value.xm3 || null,
      xm4: editForm.value.xm4 || null,
      xm5: editForm.value.xm5 || null,
      xm6: editForm.value.xm6 || null,
      xm7: editForm.value.xm7 || null,
      xm8: editForm.value.xm8 || null,
      xm9: editForm.value.xm9 || null,
      xm10: editForm.value.xm10 || null,
      xm: editForm.value.yanwang === '0' ? '佛光注照' : '佛光接引',
      paiwei_type: editForm.value.paiwei_type || null,
      yanwang: parseInt(editForm.value.yanwang),
      amount: parseFloat(editForm.value.amount) || 0,
      djdate: editForm.value.djdate || null,
      prt: parseInt(editForm.value.prt),
      remarks: editForm.value.remarks || null
    }
    await fahuiRecordApi.update(editForm.value.id, submitData)
    ElMessage.success('修改成功')
    editVisible.value = false
    fetchData()
  } catch (error) {
    if (error !== false) {
      console.error('修改失败:', error)
      ElMessage.error('修改失败')
    }
  } finally {
    editLoading.value = false
  }
}

const handlePreview = (row) => {
  previewData.value = row
  previewVisible.value = true
}

const handlePrint = async (row) => {
  doSilentPrint([row])
}

const openPdfForPrint = async (records, templateId) => {
  try {
    const response = await printerTemplateApi.generatePdf({
      template_id: templateId,
      records: records
    })
    const blob = new Blob([response], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  } catch (error) {
    console.error('PDF生成失败:', error)
    ElMessage.error('PDF生成失败')
  }
}



const handlePrintSelected = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要打印的记录')
    return
  }
  batchPrintVisible.value = true
}

const confirmBatchPrint = async () => {
  if (!selectedTemplateId.value) {
    ElMessage.warning('请选择打印模板')
    return
  }
  batchPrintLoading.value = true
  try {
    const records = selectedRows.value.map(row => ({
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
      zuoweinum: row.zuoweinum,
      paiwei_type: row.paiwei_type,
      shizhu_name: row.施主姓名
    }))
    await printerTemplateApi.silentPrint({
      template_id: selectedTemplateId.value,
      records: records
    })
    for (const row of selectedRows.value) {
      if (row.prt !== 1) {
        await fahuiRecordApi.update(row.id, { prt: 1 })
      }
    }
    batchPrintVisible.value = false
    ElMessage.success(`已发送 ${selectedRows.value.length} 条打印任务`)
    fetchData()
  } catch (error) {
    console.error('批量打印失败:', error)
    ElMessage.error(error.response?.data?.detail || '批量打印失败')
  } finally {
    batchPrintLoading.value = false
  }
}

const handleMarkPrinted = async () => {
  try {
    await ElMessageBox.confirm(`确定要将选中的 ${selectedRows.value.length} 条记录标记为已打印吗？`, '提示', { type: 'warning' })
    for (const row of selectedRows.value) {
      if (row.prt !== 1) {
        await fahuiRecordApi.update(row.id, { prt: 1 })
      }
    }
    ElMessage.success('标记成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') console.error('标记失败:', error)
  }
}

const handleMarkUnprinted = async () => {
  try {
    await ElMessageBox.confirm(`确定要将选中的 ${selectedRows.value.length} 条记录标记为未打印吗？`, '提示', { type: 'warning' })
    for (const row of selectedRows.value) {
      if (row.prt !== 0) {
        await fahuiRecordApi.update(row.id, { prt: 0 })
      }
    }
    ElMessage.success('标记成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') console.error('标记失败:', error)
  }
}

const getDefaultTemplateId = () => {
  const defaultTemplate = templateList.value.find(t => t.是否默认 === 1)
  if (defaultTemplate) return defaultTemplate.id
  if (templateList.value.length > 0) return templateList.value[0].id
  return null
}

const doSilentPrint = async (rows) => {
  const templateId = getDefaultTemplateId()
  if (!templateId) {
    ElMessage.warning('没有可用的打印模板')
    return
  }
  try {
    silentPrintLoading.value = true
    const records = rows.map(row => ({
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
      zuoweinum: row.zuoweinum,
      paiwei_type: row.paiwei_type,
      shizhu_name: row.施主姓名
    }))
    await printerTemplateApi.silentPrint({
      template_id: templateId,
      records: records
    })
    for (const row of rows) {
      if (row.prt !== 1) {
        await fahuiRecordApi.update(row.id, { prt: 1 })
      }
    }
    ElMessage.success(`已发送 ${rows.length} 条静默打印任务`)
    fetchData()
  } catch (error) {
    console.error('静默打印失败:', error)
    ElMessage.error(error.response?.data?.detail || '静默打印失败')
  } finally {
    silentPrintLoading.value = false
  }
}

const handleSilentPrint = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要打印的记录')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要使用默认模板静默打印 ${selectedRows.value.length} 条记录吗？`,
      '静默打印确认',
      { type: 'warning' }
    )
    doSilentPrint(selectedRows.value)
  } catch {
    // cancelled
  }
}

const handleSilentPrintSingle = async (row) => {
  try {
    await ElMessageBox.confirm(
      '确定要使用默认模板静默打印此记录吗？',
      '静默打印确认',
      { type: 'warning' }
    )
    doSilentPrint([row])
  } catch {
    // cancelled
  }
}

watch(() => props.type, () => {
  selectedTemplateId.value = null
  currentPage.value = 1
  fetchTemplateList()
  fetchData()
})

onMounted(() => {
  fetchFahuiList()
  fetchTemplateList()
  fetchData()
})
</script>

<style scoped>
.sticky-info { position: sticky; top: 0; z-index: 10; background: #fff; padding: 8px 0; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.info-tag { display: inline-flex; }
.filter-bar { margin-bottom: 15px; display: flex; align-items: center; }
.statistics { margin-top: 15px; padding: 10px; background: #f5f7fa; border-radius: 4px; color: #606266; }
.pagination { margin-top: 15px; display: flex; justify-content: flex-end; }

</style>
