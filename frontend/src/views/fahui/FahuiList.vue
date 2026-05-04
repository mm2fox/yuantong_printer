<template>
  <div class="fahui-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>法会管理</span>
          <div>
            <el-button type="primary" @click="handleAddFahui">新增法会</el-button>
            <el-button type="success" @click="handleRegister">法会登记</el-button>
          </div>
        </div>
      </template>
      
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索法会名称"
          style="width: 200px"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-select v-model="searchStatus" placeholder="状态" clearable style="width: 120px; margin-left: 10px" @change="handleSearch">
          <el-option label="进行中" value="进行中" />
          <el-option label="已完成" value="已完成" />
        </el-select>
        <el-button type="primary" style="margin-left: 10px" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>
      
      <el-table :data="filteredData" v-loading="loading" stripe>
        <el-table-column prop="法会名称" label="法会名称" min-width="150" />
        <el-table-column prop="开始日期" label="开始日期" width="110">
          <template #default="{ row }">
            {{ row.开始日期 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="截止日期" label="截止日期" width="110">
          <template #default="{ row }">
            {{ row.截止日期 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="功德金大" label="功德金(大)" width="100">
          <template #default="{ row }">
            {{ row.功德金大 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="功德金中" label="功德金(中)" width="100">
          <template #default="{ row }">
            {{ row.功德金中 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="功德金小" label="功德金(小)" width="100">
          <template #default="{ row }">
            {{ row.功德金小 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="完成状态" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.完成状态 === '已完成' ? 'success' : 'warning'">
              {{ row.完成状态 || '进行中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="备注" label="备注" min-width="120">
          <template #default="{ row }">
            {{ row.备注 || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="success" link @click="handleRegisterFahui(row)">登记</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="statistics">
        <span>共 {{ filteredData.length }} 个法会</span>
      </div>
    </el-card>
    
    <el-dialog
      v-model="fahuiDialogVisible"
      :title="isEditFahui ? '编辑法会' : '新增法会'"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="fahuiFormRef"
        :model="fahuiFormData"
        :rules="fahuiFormRules"
        label-width="100px"
      >
        <el-form-item label="法会名称" prop="法会名称">
          <el-input v-model="fahuiFormData.法会名称" placeholder="请输入法会名称" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="fahuiFormData.开始日期"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="fahuiFormData.截止日期"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="功德金大">
              <el-input v-model="fahuiFormData.功德金大" placeholder="金额" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="功德金中">
              <el-input v-model="fahuiFormData.功德金中" placeholder="金额" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="功德金小">
              <el-input v-model="fahuiFormData.功德金小" placeholder="金额" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="完成状态">
          <el-select v-model="fahuiFormData.完成状态" style="width: 100%">
            <el-option label="进行中" value="进行中" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="fahuiFormData.备注" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="fahuiDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitFahui" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="registerDialogVisible"
      title="法会登记"
      width="650px"
      destroy-on-close
    >
      <el-form
        ref="registerFormRef"
        :model="registerFormData"
        :rules="registerFormRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="法会名称" prop="fahui_id">
              <el-select v-model="registerFormData.fahui_id" style="width: 100%" @change="handleFahuiChange" filterable>
                <el-option
                  v-for="item in tableData"
                  :key="item.id"
                  :label="item.法会名称"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="施主选择" prop="fahui_user_id">
              <el-select
                v-model="registerFormData.fahui_user_id"
                filterable
                remote
                :remote-method="handleShizhuSearch"
                :loading="shizhuLoading"
                placeholder="搜索选择施主"
                style="width: 100%"
              >
                <el-option
                  v-for="item in shizhuList"
                  :key="item.id"
                  :label="`${item.施主姓名} (${item.施主编号})`"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">姓名信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名1">
              <el-input v-model="registerFormData.xm1" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名2">
              <el-input v-model="registerFormData.xm2" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名3">
              <el-input v-model="registerFormData.xm3" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名4">
              <el-input v-model="registerFormData.xm4" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="姓名5">
          <el-input v-model="registerFormData.xm5" />
        </el-form-item>
        
        <el-divider content-position="left">登记信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="牌位类型">
              <el-select v-model="registerFormData.paiwei_type" style="width: 100%">
                <el-option label="大牌" value="大牌" />
                <el-option label="中牌" value="中牌" />
                <el-option label="小牌" value="小牌" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型">
              <el-radio-group v-model="registerFormData.yanwang">
                <el-radio value="0">延生</el-radio>
                <el-radio value="1">往生</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="金额" prop="amount">
          <el-input-number v-model="registerFormData.amount" :min="0" :precision="2" style="width: 200px" />
          <span style="margin-left: 10px">元</span>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input v-model="registerFormData.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="registerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitRegister" :loading="submitLoading">保存</el-button>
        <el-button type="success" @click="handleSubmitAndContinue" :loading="submitLoading">保存并继续</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fahuiInfoApi } from '@/api/fahuiInfo'
import { fahuiUserApi } from '@/api/fahuiUsers'
import { fahuiRecordApi } from '@/api/fahuiRecords'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const shizhuList = ref([])
const shizhuLoading = ref(false)
const shizhuSearchKeyword = ref('')

const searchKeyword = ref('')
const searchStatus = ref('')

const fahuiDialogVisible = ref(false)
const registerDialogVisible = ref(false)
const isEditFahui = ref(false)
const fahuiFormRef = ref(null)
const registerFormRef = ref(null)

const fahuiFormData = reactive({
  id: null,
  法会名称: '',
  开始日期: '',
  截止日期: '',
  功德金大: '',
  功德金中: '',
  功德金小: '',
  完成状态: '进行中',
  备注: ''
})

const registerFormData = reactive({
  fahui_id: '',
  fahui_name: '',
  fahui_user_id: null,
  xm1: '',
  xm2: '',
  xm3: '',
  xm4: '',
  xm5: '',
  paiwei_type: '中牌',
  yanwang: '0',
  amount: 0,
  remarks: ''
})

const fahuiFormRules = {
  法会名称: [{ required: true, message: '请输入法会名称', trigger: 'blur' }]
}

const registerFormRules = {
  fahui_id: [{ required: true, message: '请选择法会', trigger: 'change' }],
  fahui_user_id: [{ required: true, message: '请选择施主', trigger: 'change' }]
}

const filteredData = computed(() => {
  let data = tableData.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    data = data.filter(item => 
      item.法会名称?.toLowerCase().includes(keyword)
    )
  }
  if (searchStatus.value) {
    data = data.filter(item => (item.完成状态 || '进行中') === searchStatus.value)
  }
  return data
})

const handleSearch = () => {
}

const handleReset = () => {
  searchKeyword.value = ''
  searchStatus.value = ''
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await fahuiInfoApi.getList()
    tableData.value = res
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
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

const resetFahuiForm = () => {
  Object.assign(fahuiFormData, {
    id: null,
    法会名称: '',
    开始日期: '',
    截止日期: '',
    功德金大: '',
    功德金中: '',
    功德金小: '',
    完成状态: '进行中',
    备注: ''
  })
}

const resetRegisterForm = () => {
  Object.assign(registerFormData, {
    fahui_id: '',
    fahui_name: '',
    fahui_user_id: null,
    xm1: '',
    xm2: '',
    xm3: '',
    xm4: '',
    xm5: '',
    paiwei_type: '中牌',
    yanwang: '0',
    amount: 0,
    remarks: ''
  })
}

const handleAddFahui = () => {
  resetFahuiForm()
  isEditFahui.value = false
  fahuiDialogVisible.value = true
}

const handleEdit = (row) => {
  resetFahuiForm()
  isEditFahui.value = true
  Object.assign(fahuiFormData, row)
  fahuiDialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该法会吗？', '提示', {
      type: 'warning'
    })
    await fahuiInfoApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleSubmitFahui = async () => {
  if (!fahuiFormRef.value) return
  
  await fahuiFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEditFahui.value) {
          await fahuiInfoApi.update(fahuiFormData.id, fahuiFormData)
          ElMessage.success('更新成功')
        } else {
          await fahuiInfoApi.create(fahuiFormData)
          ElMessage.success('创建成功')
        }
        fahuiDialogVisible.value = false
        fetchData()
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleRegister = () => {
  resetRegisterForm()
  registerDialogVisible.value = true
  fetchShizhuList()
}

const handleRegisterFahui = (row) => {
  resetRegisterForm()
  registerFormData.fahui_id = row.id
  registerFormData.fahui_name = row.法会名称
  registerDialogVisible.value = true
  fetchShizhuList()
}

const handleFahuiChange = (val) => {
  const fahui = tableData.value.find(item => item.id === val)
  if (fahui) {
    registerFormData.fahui_name = fahui.法会名称
  }
}

const submitRegister = async () => {
  if (!registerFormRef.value) return false
  
  return new Promise((resolve) => {
    registerFormRef.value.validate(async (valid) => {
      if (valid) {
        submitLoading.value = true
        try {
          const submitData = {
            ...registerFormData,
            yanwang: parseInt(registerFormData.yanwang)
          }
          await fahuiRecordApi.create(submitData)
          ElMessage.success('登记成功')
          resolve(true)
        } catch (error) {
          console.error('登记失败:', error)
          resolve(false)
        } finally {
          submitLoading.value = false
        }
      } else {
        resolve(false)
      }
    })
  })
}

const handleSubmitRegister = async () => {
  const success = await submitRegister()
  if (success) {
    registerDialogVisible.value = false
  }
}

const handleSubmitAndContinue = async () => {
  const success = await submitRegister()
  if (success) {
    const currentFahuiId = registerFormData.fahui_id
    resetRegisterForm()
    registerFormData.fahui_id = currentFahuiId
    const fahui = tableData.value.find(item => item.id === currentFahuiId)
    if (fahui) {
      registerFormData.fahui_name = fahui.法会名称
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.fahui-list {
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
}

.statistics {
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
}
</style>
