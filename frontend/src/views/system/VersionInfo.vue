<template>
  <div class="version-info">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>版本信息</span>
          <div>
            <el-button type="success" @click="handleImportBuildInfo" :loading="importLoading">导入构建信息</el-button>
          </div>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe max-height="500">
        <el-table-column prop="version" label="版本号" width="100" />
        <el-table-column prop="git_commit" label="Git Commit" width="120">
          <template #default="{ row }">
            <el-tooltip :content="row.git_commit" placement="top" v-if="row.git_commit">
              <span class="commit-hash">{{ row.git_commit?.substring(0, 8) }}</span>
            </el-tooltip>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="git_branch" label="分支" width="120" />
        <el-table-column prop="git_author" label="提交者" width="120" />
        <el-table-column prop="git_message" label="提交信息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="git_date" label="提交时间" width="180" />
        <el-table-column prop="build_time" label="构建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.build_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="change_summary" label="变更摘要" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="statistics">
        <span>共 {{ totalCount }} 条版本记录</span>
      </div>
    </el-card>

    <el-dialog v-model="detailDialogVisible" title="版本详情" width="600px">
      <el-descriptions :column="1" border v-if="currentVersion">
        <el-descriptions-item label="版本号">{{ currentVersion.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Git Commit">{{ currentVersion.git_commit || '-' }}</el-descriptions-item>
        <el-descriptions-item label="分支">{{ currentVersion.git_branch || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交者">{{ currentVersion.git_author || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交信息">{{ currentVersion.git_message || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ currentVersion.git_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="构建时间">{{ formatDateTime(currentVersion.build_time) }}</el-descriptions-item>
        <el-descriptions-item label="变更摘要">
          <div class="change-summary">{{ currentVersion.change_summary || '-' }}</div>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { versionInfoApi } from '@/api/versionInfo'

const loading = ref(false)
const importLoading = ref(false)
const tableData = ref([])
const totalCount = ref(0)
const detailDialogVisible = ref(false)
const currentVersion = ref(null)

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  return datetime.replace('T', ' ').substring(0, 19)
}

const fetchData = async () => {
  loading.value = true
  try {
    const [listRes, countRes] = await Promise.all([
      versionInfoApi.getList(),
      versionInfoApi.getCount()
    ])
    tableData.value = listRes
    totalCount.value = countRes.count
  } catch (error) {
    console.error('获取版本信息失败:', error)
    ElMessage.error('获取版本信息失败')
  } finally {
    loading.value = false
  }
}

const handleImportBuildInfo = async () => {
  importLoading.value = true
  try {
    const res = await versionInfoApi.importBuildInfo()
    ElMessage.success(res.message || '导入成功')
    fetchData()
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.warning(error.response.data.detail)
    } else {
      ElMessage.error('导入构建信息失败')
    }
  } finally {
    importLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除版本 ${row.version || row.git_commit?.substring(0, 8) || ''} 的记录吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await versionInfoApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.version-info {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.commit-hash {
  font-family: 'Courier New', Courier, monospace;
  color: #409eff;
  cursor: pointer;
}

.statistics {
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
}

.change-summary {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}
</style>
