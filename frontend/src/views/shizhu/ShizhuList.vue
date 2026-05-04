<template>
  <div class="shizhu-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>施主管理</span>
          <el-button type="primary" @click="handleAdd">新增施主</el-button>
        </div>
      </template>
      
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索施主姓名/编号/电话"
          style="width: 250px"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-select v-model="searchGongdezhu" placeholder="功德主" clearable style="width: 100px; margin-left: 10px" @change="handleSearch">
          <el-option label="是" value="1" />
          <el-option label="否" value="0" />
        </el-select>
        <el-button type="primary" style="margin-left: 10px" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>
      
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="施主编号" label="施主编号" width="120" />
        <el-table-column prop="施主姓名" label="施主姓名" width="120">
          <template #default="{ row }">
            <div v-if="editingRowId === row.id" style="display: flex; align-items: center;">
              <el-input
                ref="editInputRef"
                v-model="row.施主姓名"
                size="small"
                class="no-border-input"
                @blur="handleInlineEdit(row)"
                @keyup.enter="$event.target.blur()"
              />
            </div>
            <span v-else class="shizhu-name-text" @dblclick="enableEdit(row)">
              {{ row.施主姓名 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="电话" label="电话" width="130">
          <template #default="{ row }">
            {{ row.电话 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="地址" label="地址" min-width="150">
          <template #default="{ row }">
            {{ row.地址 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="功德主" label="功德主" width="80">
          <template #default="{ row }">
            <el-tag :type="row.功德主 === 1 ? 'success' : 'info'">
              {{ row.功德主 === 1 ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="登记人" label="登记人" width="80">
          <template #default="{ row }">
            {{ row.登记人 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="登记时间" label="登记时间" width="110">
          <template #default="{ row }">
            {{ row.登记时间 ? row.登记时间.substring(0, 10) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewRecords(row)">记录</el-button>
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
    </el-card>
    
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑施主' : '新增施主'"
      width="700px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="施主编号" prop="施主编号">
              <el-input v-model="formData.施主编号" placeholder="自动生成" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="施主姓名" prop="施主姓名">
              <el-input v-model="formData.施主姓名" placeholder="请输入施主姓名" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="formData.电话" placeholder="请输入电话" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="地址">
          <el-input v-model="formData.地址" placeholder="请输入地址" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="功德主">
              <el-switch
                v-model="formData.功德主"
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
              <el-input v-model="formData.佛光接引一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光接引二">
              <el-input v-model="formData.佛光接引二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光接引三">
              <el-input v-model="formData.佛光接引三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光接引四">
              <el-input v-model="formData.佛光接引四" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">阳上</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上一">
              <el-input v-model="formData.阳上一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上二">
              <el-input v-model="formData.阳上二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上三">
              <el-input v-model="formData.阳上三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上四">
              <el-input v-model="formData.阳上四" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上五">
              <el-input v-model="formData.阳上五" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上六">
              <el-input v-model="formData.阳上六" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">佛光注照</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光注照一">
              <el-input v-model="formData.佛光注照一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光注照二">
              <el-input v-model="formData.佛光注照二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光注照三">
              <el-input v-model="formData.佛光注照三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光注照四">
              <el-input v-model="formData.佛光注照四" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="备注">
          <el-input v-model="formData.备注" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="recordsDialogVisible"
      :title="`施主【${currentShizhu.施主姓名}】的法会记录`"
      width="900px"
    >
      <el-table :data="shizhuRecords" v-loading="recordsLoading" stripe max-height="400">
        <el-table-column prop="fahui_name" label="法会名称" width="120" />
        <el-table-column prop="paiwei_type" label="牌位类型" width="80" />
        <el-table-column prop="amount" label="金额" width="100">
          <template #default="{ row }">
            {{ row.amount?.toFixed(2) }} 元
          </template>
        </el-table-column>
        <el-table-column prop="yanwang" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.yanwang === 0 ? 'success' : 'danger'">
              {{ row.yanwang === 0 ? '延生' : '往生' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="djdate" label="登记日期" width="110" />
        <el-table-column prop="经办人" label="经办人" width="80">
          <template #default="{ row }">
            {{ row.经办人 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="prt" label="打印状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.prt === 1 ? 'success' : 'info'">
              {{ row.prt === 1 ? '已打印' : '未打印' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remarks" label="备注" min-width="100">
          <template #default="{ row }">
            {{ row.remarks || '-' }}
          </template>
        </el-table-column>
      </el-table>
      <div class="records-statistics">
        <span>共 {{ shizhuRecords.length }} 条记录</span>
        <span style="margin-left: 20px">金额合计: {{ recordsTotalAmount.toFixed(2) }} 元</span>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fahuiUserApi } from '@/api/fahuiUsers'
import { fahuiRecordApi } from '@/api/fahuiRecords'

const loading = ref(false)
const submitLoading = ref(false)
const allData = ref([])
const searchKeyword = ref('')
const searchGongdezhu = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const editingRowId = ref(null)
const editInputRef = ref(null)

const recordsDialogVisible = ref(false)
const recordsLoading = ref(false)
const shizhuRecords = ref([])
const currentShizhu = ref({})

const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const recordsTotalAmount = computed(() => {
  return shizhuRecords.value.reduce((sum, item) => sum + (item.amount || 0), 0)
})

const formData = reactive({
  id: null,
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

const formRules = {
  施主姓名: [{ required: true, message: '请输入施主姓名', trigger: 'blur' }]
}

const filteredData = computed(() => {
  let data = allData.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    data = data.filter(item => 
      item.施主姓名?.toLowerCase().includes(keyword) ||
      item.施主编号?.toLowerCase().includes(keyword) ||
      item.电话?.includes(keyword)
    )
  }
  if (searchGongdezhu.value !== '' && searchGongdezhu.value !== null) {
    data = data.filter(item => item.功德主 === parseInt(searchGongdezhu.value))
  }
  return data
})

const tableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  total.value = filteredData.value.length
  return filteredData.value.slice(start, end)
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await fahuiUserApi.getList(undefined, 500)
    allData.value = res
    total.value = res.length
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleReset = () => {
  searchKeyword.value = ''
  searchGongdezhu.value = ''
  currentPage.value = 1
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

const resetForm = () => {
  Object.assign(formData, {
    id: null,
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
}

const handleAdd = async () => {
  resetForm()
  isEdit.value = false
  try {
    const res = await fahuiUserApi.generateCode()
    formData.施主编号 = res.code
  } catch (error) {
    console.error('生成编号失败:', error)
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  resetForm()
  isEdit.value = true
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该施主吗？', '提示', {
      type: 'warning'
    })
    await fahuiUserApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const enableEdit = (row) => {
  editingRowId.value = row.id
}

const handleInlineEdit = async (row) => {
  if (!row.施主姓名 || !row.施主姓名.trim()) {
    ElMessage.warning('施主姓名不能为空')
    return
  }
  try {
    await fahuiUserApi.update(row.id, { 施主姓名: row.施主姓名.trim() })
    row.施主姓名 = row.施主姓名.trim()
  } catch (error) {
    console.error('更新施主姓名失败:', error)
    ElMessage.error('更新失败')
  } finally {
    editingRowId.value = null
  }
}

const handleViewRecords = async (row) => {
  currentShizhu.value = row
  recordsDialogVisible.value = true
  recordsLoading.value = true
  try {
    const res = await fahuiRecordApi.queryByShizhu({ shizhu_code: row.施主编号 })
    shizhuRecords.value = res.records || []
  } catch (error) {
    console.error('获取记录失败:', error)
    ElMessage.error('获取法会记录失败')
  } finally {
    recordsLoading.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEdit.value) {
          await fahuiUserApi.update(formData.id, formData)
          ElMessage.success('更新成功')
        } else {
          await fahuiUserApi.create(formData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchData()
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.shizhu-list {
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

.pagination-container {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.records-statistics {
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
}

.no-border-input :deep(.el-input__wrapper) {
  box-shadow: none;
  border: none;
  background: transparent;
}
.no-border-input :deep(.el-input__wrapper:hover) {
  box-shadow: none;
  border: none;
}
.no-border-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: none;
  border: none;
}

.shizhu-name-text {
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 2px;
  transition: background-color 0.2s;
}
.shizhu-name-text:hover {
  background-color: #f0f0f0;
}
</style>
