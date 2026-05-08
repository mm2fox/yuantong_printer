<template>
  <div class="fahui-record-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>法会登记</span>
          <el-button type="primary" @click="handleAdd">新增登记</el-button>
        </div>
      </template>
      
      <div class="search-bar">
        <el-select v-model="searchForm.fahui_name" placeholder="法会名称" clearable style="width: 150px" @change="handleSearch">
          <el-option v-for="item in fahuiList" :key="item.id" :label="item.法会名称" :value="item.法会名称" />
        </el-select>
        <el-input v-model="searchForm.shizhu_name" placeholder="施主姓名" clearable style="width: 120px; margin-left: 10px" @keyup.enter="handleSearch" />
        <el-select v-model="searchForm.paiwei_type" placeholder="牌位类型" clearable style="width: 100px; margin-left: 10px" @change="handleSearch">
          <el-option label="大牌" value="大牌" />
          <el-option label="中牌" value="中牌" />
          <el-option label="小牌" value="小牌" />
        </el-select>
        <el-select v-model="searchForm.yanwang" placeholder="类型" clearable style="width: 90px; margin-left: 10px" @change="handleSearch">
          <el-option label="延生" value="0" />
          <el-option label="往生" value="1" />
        </el-select>
        <el-select v-model="searchForm.prt" placeholder="打印状态" clearable style="width: 100px; margin-left: 10px" @change="handleSearch">
          <el-option label="未打印" value="0" />
          <el-option label="已打印" value="1" />
        </el-select>
        <el-button type="primary" style="margin-left: 10px" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>
      
      <el-table :data="tableData" v-loading="loading" stripe max-height="500">
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
      <div v-if="formData.fahui_name || formData.fahui_user_id" class="sticky-info">
        <span v-if="formData.fahui_name" class="info-tag">
          <el-tag type="primary" size="large">{{ formData.fahui_name }}</el-tag>
        </span>
        <span v-if="selectedShizhuName" class="info-tag">
          <el-tag type="success" size="large">{{ selectedShizhuName }}</el-tag>
        </span>
        <el-tag :type="formData.yanwang === '0' ? 'warning' : 'danger'" size="large">
          {{ formData.yanwang === '0' ? '延生' : '往生' }}
        </el-tag>
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
                <el-select v-model="formData.fahui_name" style="flex: 1" filterable @change="handleFahuiSelect">
                  <el-option v-for="item in fahuiList" :key="item.id" :label="item.法会名称" :value="item.法会名称" />
                </el-select>
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
                <el-select
                  v-model="formData.fahui_user_id"
                  filterable
                  remote
                  :remote-method="handleShizhuSearch"
                  :loading="shizhuLoading"
                  placeholder="搜索选择施主"
                  style="flex: 1"
                  @change="handleShizhuSelect"
                >
                  <el-option
                    v-for="item in shizhuList"
                    :key="item.id"
                    :label="`${item.施主姓名} (${item.施主编号})`"
                    :value="item.id"
                  />
                </el-select>
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
import { ref, reactive, onMounted, computed } from 'vue'
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
const shizhuSearchKeyword = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const selectedShizhuName = computed(() => {
  if (!formData.fahui_user_id) return ''
  const shizhu = shizhuList.value.find(item => item.id === formData.fahui_user_id)
  return shizhu ? `${shizhu.施主姓名} (${shizhu.施主编号})` : ''
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
    const res = await fahuiUserApi.getList(keyword || undefined, 50)
    shizhuList.value = res
  } catch (error) {
    console.error('获取施主列表失败:', error)
  } finally {
    shizhuLoading.value = false
  }
}

const handleShizhuSearch = (query) => {
  shizhuSearchKeyword.value = query
  fetchShizhuList(query)
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
}

const handleAdd = () => {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
  fetchShizhuList()
}

const handleEdit = (row) => {
  resetForm()
  isEdit.value = true
  Object.assign(formData, {
    id: row.id,
    fahui_id: row.fahui_id,
    fahui_name: row.fahui_name,
    fahui_user_id: row.fahui_user_id,
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
  dialogVisible.value = true
  fetchShizhuList()
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

const handleFahuiSelect = (val) => {
  const fahui = fahuiList.value.find(item => item.法会名称 === val)
  if (fahui) {
    formData.fahui_id = fahui.id
  }
}

const handleShizhuSelect = (val) => {
  if (!val) {
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
  const shizhu = shizhuList.value.find(item => item.id === val)
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
    const shizhu = shizhuList.value.find(item => item.id === formData.fahui_user_id)
    if (shizhu) {
      fillNamesFromShizhu(shizhu)
    }
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
        await fetchShizhuList(shizhuSearchKeyword.value)
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
