<template>
  <div class="user-data">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isAdmin ? '用户数据' : '我的操作日志' }}</span>
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
        <el-form-item label="用户名" v-if="isAdmin">
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
        <el-table-column prop="用户名" label="用户名" width="100" v-if="isAdmin" />
        <el-table-column prop="操作类型" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTagType(row.操作类型)">{{ row.操作类型 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="操作内容" label="操作内容" min-width="400" show-overflow-tooltip />
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      
      <div class="statistics">
        <span>共 {{ totalCount }} 条操作记录</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { systemLogApi } from '@/api/systemLogs'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const loading = ref(false)
const tableData = ref([])
const totalCount = ref(0)

const isAdmin = computed(() => {
  return userStore.userInfo?.role === '管理员'
})

const searchForm = reactive({
  start_date: '',
  end_date: '',
  用户名: '',
  操作类型: ''
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
    if (searchForm.操作类型) params.操作类型 = searchForm.操作类型
    
    let logsRes, countRes
    if (isAdmin.value) {
      if (searchForm.用户名) params.用户名 = searchForm.用户名
      const [logs, count] = await Promise.all([
        systemLogApi.getList(params),
        systemLogApi.getCount(params)
      ])
      logsRes = logs
      countRes = count
    } else {
      const [logs, count] = await Promise.all([
        systemLogApi.getMyLogs(params),
        systemLogApi.getMyLogCount(params)
      ])
      logsRes = logs
      countRes = count
    }
    
    tableData.value = logsRes
    totalCount.value = countRes.count
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
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

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.user-data {
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
