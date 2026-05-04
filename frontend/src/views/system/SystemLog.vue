<template>
  <div class="system-log">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <el-button type="danger" @click="handleClearLogs">清理日志</el-button>
        </div>
      </template>
      
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="searchForm.start_date"
            type="date"
            placeholder="开始日期"
            value-format="YYYY-MM-DD"
            style="width: 140px"
          />
          <span style="margin: 0 5px">-</span>
          <el-date-picker
            v-model="searchForm.end_date"
            type="date"
            placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 140px"
          />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="searchForm.用户名" placeholder="输入用户名" clearable style="width: 120px" />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select v-model="searchForm.操作类型" placeholder="全部" clearable style="width: 120px">
            <el-option label="登录" value="登录" />
            <el-option label="登录失败" value="登录失败" />
            <el-option label="登出" value="登出" />
            <el-option label="新增" value="新增" />
            <el-option label="修改" value="修改" />
            <el-option label="删除" value="删除" />
            <el-option label="查询" value="查询" />
            <el-option label="打印" value="打印" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      
      <el-table :data="tableData" v-loading="loading" stripe max-height="500">
        <el-table-column prop="用户名" label="用户名" width="100" />
        <el-table-column prop="操作类型" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTagType(row.操作类型)">{{ row.操作类型 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="操作内容" label="操作内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      
      <div class="statistics">
        <span>共 {{ totalCount }} 条日志记录</span>
      </div>
    </el-card>
    
    <el-dialog v-model="clearDialogVisible" title="清理日志" width="400px">
      <el-form :model="clearForm" label-width="80px">
        <el-form-item label="清理范围">
          <el-radio-group v-model="clearForm.type">
            <el-radio value="all">全部日志</el-radio>
            <el-radio value="date">按日期范围</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <template v-if="clearForm.type === 'date'">
          <el-form-item label="开始日期">
            <el-date-picker
              v-model="clearForm.start_date"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-date-picker
              v-model="clearForm.end_date"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <el-button @click="clearDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmClearLogs" :loading="clearLoading">确认清理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemLogApi } from '@/api/systemLogs'

const loading = ref(false)
const clearLoading = ref(false)
const tableData = ref([])
const totalCount = ref(0)
const clearDialogVisible = ref(false)

const searchForm = reactive({
  start_date: '',
  end_date: '',
  用户名: '',
  操作类型: ''
})

const clearForm = reactive({
  type: 'all',
  start_date: '',
  end_date: ''
})

const getTagType = (type) => {
  const typeMap = {
    '登录': 'success',
    '登录失败': 'danger',
    '登出': 'info',
    '新增': 'primary',
    '修改': 'warning',
    '删除': 'danger',
    '查询': '',
    '打印': 'success'
  }
  return typeMap[type] || ''
}

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  return datetime.replace('T', ' ').substring(0, 19)
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {}
    if (searchForm.start_date) params.start_date = searchForm.start_date
    if (searchForm.end_date) params.end_date = searchForm.end_date
    if (searchForm.用户名) params.用户名 = searchForm.用户名
    if (searchForm.操作类型) params.操作类型 = searchForm.操作类型
    
    const [logsRes, countRes] = await Promise.all([
      systemLogApi.getList(params),
      systemLogApi.getCount(params)
    ])
    
    tableData.value = logsRes
    totalCount.value = countRes.count
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  fetchData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    start_date: '',
    end_date: '',
    用户名: '',
    操作类型: ''
  })
  fetchData()
}

const handleClearLogs = () => {
  clearForm.type = 'all'
  clearForm.start_date = ''
  clearForm.end_date = ''
  clearDialogVisible.value = true
}

const confirmClearLogs = async () => {
  if (clearForm.type === 'date') {
    if (!clearForm.start_date || !clearForm.end_date) {
      ElMessage.warning('请选择日期范围')
      return
    }
  }
  
  try {
    await ElMessageBox.confirm(
      clearForm.type === 'all' 
        ? '确定要清理全部日志吗？此操作不可恢复！' 
        : '确定要清理选定日期范围内的日志吗？此操作不可恢复！',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    clearLoading.value = true
    
    const deleteData = clearForm.type === 'all' 
      ? { start_date: '2000-01-01', end_date: '2099-12-31' }
      : { start_date: clearForm.start_date, end_date: clearForm.end_date }
    
    const res = await systemLogApi.delete(deleteData)
    ElMessage.success(res.message)
    clearDialogVisible.value = false
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清理日志失败:', error)
      ElMessage.error('清理日志失败')
    }
  } finally {
    clearLoading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.system-log {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 15px;
}

.statistics {
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
}
</style>
