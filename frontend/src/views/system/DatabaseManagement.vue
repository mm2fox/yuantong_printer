<template>
  <div class="database-management">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>数据库信息</span>
              <el-button type="primary" size="small" @click="loadDatabaseInfo" :loading="loading">
                刷新
              </el-button>
            </div>
          </template>
          
          <div v-if="dbInfo" class="info-content">
            <div class="info-item">
              <label>数据库路径:</label>
              <span>{{ dbInfo.database_path }}</span>
            </div>
            <div class="info-item">
              <label>数据库大小:</label>
              <span>{{ dbInfo.database_size_mb }} MB ({{ dbInfo.database_size }} 字节)</span>
            </div>
            <div class="info-item">
              <label>备份目录:</label>
              <span>{{ dbInfo.backup_dir }}</span>
            </div>
            
            <el-divider>表信息</el-divider>
            
            <el-table :data="dbInfo.tables" border stripe max-height="300">
              <el-table-column prop="name" label="表名" />
              <el-table-column prop="count" label="记录数" width="100" />
            </el-table>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="operations-card">
          <template #header>
            <span>数据库操作</span>
          </template>
          
          <div class="operations">
            <div class="operation-item">
              <h3>导入Excel</h3>
              <p>导入Excel文件中的施主和法会记录数据（自动关联"历史法会"，不存在则创建；施主按编号去重）</p>
              <div class="import-row">
                <el-upload
                  ref="uploadRef"
                  :auto-upload="false"
                  :show-file-list="false"
                  accept=".xls,.xlsx"
                  :on-change="handleFileChange"
                >
                  <el-button type="primary">
                    <el-icon><FolderOpened /></el-icon>
                    选择文件
                  </el-button>
                </el-upload>
                <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
                <span v-else class="file-name placeholder">未选择文件</span>
              </div>
              <div class="import-row" style="margin-top: 10px;">
                <el-button type="info" @click="handlePreviewExcel" :disabled="!selectedFile" :loading="previewLoading">
                  <el-icon><View /></el-icon>
                  预览
                </el-button>
                <el-button type="success" @click="handleImportExcel" :disabled="!selectedFile" :loading="importLoading">
                  <el-icon><Upload /></el-icon>
                  导入
                </el-button>
              </div>
            </div>
            
            <el-divider />
            
            <div class="operation-item">
              <h3>备份操作</h3>
              <p>创建当前数据库的备份文件</p>
              <el-button type="primary" @click="handleBackup" :loading="backupLoading">
                <el-icon><Download /></el-icon>
                创建备份
              </el-button>
            </div>
            
            <el-divider />
            
            <div class="operation-item">
              <h3>清空指定表</h3>
              <p>选择要清空的数据表</p>
              <div class="clear-table-row">
                <el-select v-model="selectedTable" placeholder="选择要清空的表" style="width: 200px;">
                  <el-option
                    v-for="(label, key) in clearableTables"
                    :key="key"
                    :label="label"
                    :value="key"
                  />
                </el-select>
                <el-button 
                  type="danger" 
                  @click="handleClearTable" 
                  :disabled="!selectedTable"
                  :loading="clearTableLoading"
                >
                  <el-icon><Delete /></el-icon>
                  清空选中表
                </el-button>
              </div>
            </div>
            
            <el-divider />
            
            <div class="operation-item">
              <h3>清空所有数据</h3>
              <p>清空所有业务数据(保留用户和寺庙数据)</p>
              <el-button type="danger" @click="handleClear">
                <el-icon><Delete /></el-icon>
                清空所有数据
              </el-button>
            </div>
            
            <el-divider />
            
            <div class="operation-item">
              <h3>初始化数据库</h3>
              <p>重新初始化数据库，恢复默认模板和基础数据</p>
              <el-button type="warning" @click="handleInit" :loading="initLoading">
                <el-icon><RefreshRight /></el-icon>
                初始化数据库
              </el-button>
            </div>

            <el-divider />

            <div class="operation-item">
              <h3>清理未使用图片</h3>
              <p>删除未被任何打印模板引用的图片文件，释放磁盘空间</p>
              <el-button type="warning" @click="handleCleanupImages" :loading="cleanupLoading">
                <el-icon><Delete /></el-icon>
                清理图片
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="backups-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>备份文件列表</span>
          <el-button type="primary" size="small" @click="loadBackups" :loading="backupsLoading">
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table :data="backups" border stripe v-loading="backupsLoading">
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="size_mb" label="大小(MB)" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleRestore(row.filename)">
              恢复
            </el-button>
            <el-button type="success" size="small" @click="handleDownload(row.filename)">
              下载
            </el-button>
            <el-button type="danger" size="small" @click="handleDeleteBackup(row.filename)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="backups.length === 0 && !backupsLoading" description="暂无备份文件" />
    </el-card>

    <el-dialog v-model="previewDialogVisible" title="Excel数据预览" width="80%" destroy-on-close>
      <div v-if="previewData">
        <p style="margin-bottom: 10px; color: #909399;">
          文件: {{ previewData.filename }} | 总行数: {{ previewData.total_rows }} | 以下显示前5行 | 鼠标悬停列头查看映射关系
        </p>
        <el-table :data="previewData.preview_rows" border stripe max-height="400" style="width: 100%">
          <el-table-column
            v-for="header in previewData.headers"
            :key="header"
            :prop="header"
            min-width="120"
          >
            <template #header>
              <el-tooltip :content="previewData.column_mapping?.[header] || '未知'" placement="top">
                <span :style="{ color: isMapped(header) ? '#67C23A' : '#F56C6C' }">
                  {{ header }}
                  <el-icon v-if="!isMapped(header)" style="vertical-align: middle;"><Warning /></el-icon>
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <el-dialog v-model="importResultDialogVisible" title="导入结果" width="50%">
      <div v-if="importResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="总行数">{{ importResult.total_rows }}</el-descriptions-item>
          <el-descriptions-item label="成功导入">{{ importResult.success_count }} 条</el-descriptions-item>
          <el-descriptions-item label="失败">{{ importResult.fail_count }} 条</el-descriptions-item>
          <el-descriptions-item label="新增施主">{{ importResult.new_user_count }} 人</el-descriptions-item>
          <el-descriptions-item label="复用已有施主">{{ importResult.reuse_user_count }} 人</el-descriptions-item>
          <el-descriptions-item label="新建法会">{{ importResult.new_fahui_count }} 个</el-descriptions-item>
        </el-descriptions>
        <div v-if="importResult.errors && importResult.errors.length > 0" style="margin-top: 15px;">
          <h4 style="color: #F56C6C;">错误详情:</h4>
          <ul style="color: #909399; font-size: 13px; max-height: 200px; overflow-y: auto;">
            <li v-for="(err, i) in importResult.errors" :key="i">{{ err }}</li>
          </ul>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="importResultDialogVisible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { databaseApi } from '@/api/database'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Delete, RefreshRight, Upload, View, FolderOpened, Warning } from '@element-plus/icons-vue'

const loading = ref(false)
const backupLoading = ref(false)
const backupsLoading = ref(false)
const clearTableLoading = ref(false)
const initLoading = ref(false)
const previewLoading = ref(false)
const importLoading = ref(false)
const cleanupLoading = ref(false)
const dbInfo = ref(null)
const backups = ref([])
const clearableTables = ref({})
const selectedTable = ref('')

const uploadRef = ref(null)
const selectedFile = ref(null)
const previewDialogVisible = ref(false)
const previewData = ref(null)
const importResultDialogVisible = ref(false)
const importResult = ref(null)

const handleFileChange = (uploadFile) => {
  if (!uploadFile) {
    selectedFile.value = null
    return
  }
  const name = uploadFile.name.toLowerCase()
  if (!name.endsWith('.xls') && !name.endsWith('.xlsx')) {
    ElMessage.warning('请选择 .xls 或 .xlsx 格式的文件')
    selectedFile.value = null
    return
  }
  selectedFile.value = uploadFile.raw
}

const isMapped = (header) => {
  if (!previewData.value?.column_mapping) return true
  const mapping = previewData.value.column_mapping[header] || ''
  return !mapping.startsWith('❌')
}

const loadDatabaseInfo = async () => {
  loading.value = true
  try {
    dbInfo.value = await databaseApi.getInfo()
  } catch (error) {
    ElMessage.error('获取数据库信息失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const loadBackups = async () => {
  backupsLoading.value = true
  try {
    const result = await databaseApi.getBackups()
    backups.value = result.backups
  } catch (error) {
    ElMessage.error('获取备份列表失败')
    console.error(error)
  } finally {
    backupsLoading.value = false
  }
}

const loadClearableTables = async () => {
  try {
    const result = await databaseApi.getClearableTables()
    clearableTables.value = result.tables
  } catch (error) {
    ElMessage.error('获取可清空表列表失败')
    console.error(error)
  }
}

const handlePreviewExcel = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择Excel文件')
    return
  }
  previewLoading.value = true
  try {
    const result = await databaseApi.previewExcel(selectedFile.value)
    previewData.value = result
    previewDialogVisible.value = true
  } catch (error) {
    ElMessage.error('预览Excel文件失败')
    console.error(error)
  } finally {
    previewLoading.value = false
  }
}

const handleImportExcel = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择Excel文件')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要导入文件 ${selectedFile.value.name} 吗？\n将自动关联法会"历史法会"（不存在则创建），Excel文件名会记录在法会备注中。\n施主信息将按编号去重，已存在的施主会更新信息。\n每行都会创建一条法会记录。`,
      '确认导入',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    importLoading.value = true
    const result = await databaseApi.importExcel(selectedFile.value)
    importResult.value = result
    importResultDialogVisible.value = true
    ElMessage.success(result.message)
    loadDatabaseInfo()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('导入Excel失败')
      console.error(error)
    }
  } finally {
    importLoading.value = false
  }
}

const handleBackup = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要创建数据库备份吗？',
      '确认备份',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    backupLoading.value = true
    const result = await databaseApi.backup()
    ElMessage.success(result.message)
    loadBackups()
    loadDatabaseInfo()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('备份失败')
      console.error(error)
    }
  } finally {
    backupLoading.value = false
  }
}

const handleRestore = async (filename) => {
  try {
    await ElMessageBox.confirm(
      `确定要从备份文件 ${filename} 恢复数据库吗？\n当前数据库将被备份后替换！`,
      '确认恢复',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const result = await databaseApi.restore(filename)
    ElMessage.success(result.message)
    loadDatabaseInfo()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('恢复失败')
      console.error(error)
    }
  }
}

const handleDeleteBackup = async (filename) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除备份文件 ${filename} 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const result = await databaseApi.deleteBackup(filename)
    ElMessage.success(result.message)
    loadBackups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

const handleDownload = (filename) => {
  const url = databaseApi.downloadBackup(filename)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
}

const handleClear = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空数据库吗？\n此操作将删除所有业务数据(施主、法会记录、打印模板、系统日志)！\n此操作不可恢复！',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    const result = await databaseApi.clear()
    ElMessage.success(result.message)
    loadDatabaseInfo()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败')
      console.error(error)
    }
  }
}

const handleClearTable = async () => {
  if (!selectedTable.value) {
    ElMessage.warning('请选择要清空的表')
    return
  }
  
  const tableName = clearableTables.value[selectedTable.value]
  
  try {
    await ElMessageBox.confirm(
      `确定要清空【${tableName}】表吗？\n此操作将删除该表中的所有数据！\n此操作不可恢复！`,
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    clearTableLoading.value = true
    const result = await databaseApi.clearTable(selectedTable.value)
    ElMessage.success(result.message)
    selectedTable.value = ''
    loadDatabaseInfo()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败')
      console.error(error)
    }
  } finally {
    clearTableLoading.value = false
  }
}

const handleInit = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要初始化数据库吗？\n此操作将清空所有数据并恢复默认模板和基础数据！\n此操作不可恢复！',
      '确认初始化',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    initLoading.value = true
    const result = await databaseApi.init()
    ElMessage.success(result.message)
    loadDatabaseInfo()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('初始化失败')
      console.error(error)
    }
  } finally {
    initLoading.value = false
  }
}

const handleCleanupImages = async () => {
  try {
    await ElMessageBox.confirm(
      '将删除未被任何打印模板引用的图片文件，已使用的图片不会被删除。\n确定继续？',
      '清理未使用图片',
      { type: 'warning' }
    )
    cleanupLoading.value = true
    const res = await databaseApi.cleanupImages()
    ElMessage.success(`清理完成，删除了 ${res.count} 个未使用的图片`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清理失败')
      console.error(error)
    }
  } finally {
    cleanupLoading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  loadDatabaseInfo()
  loadBackups()
  loadClearableTables()
})
</script>

<style scoped lang="scss">
.database-management {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    span {
      font-size: 18px;
      font-weight: bold;
    }
  }
  
  .info-card {
    .info-content {
      .info-item {
        margin-bottom: 15px;
        
        label {
          display: block;
          color: #08898b;
          font-size: 16px;
          margin-bottom: 5px;
          font-weight: 500;
        }
        
        span {
          color: #606266;
          font-size: 14px;
        }
      }
    }
  }
  
  .operations-card {
    .operations {
      .operation-item {
        margin-bottom: 20px;
        
        h3 {
          color: #303133;
          font-size: 16px;
          margin-bottom: 10px;
        }
        
        p {
          color: #909399;
          font-size: 14px;
          margin-bottom: 15px;
        }
        
        .clear-table-row {
          display: flex;
          gap: 10px;
          align-items: center;
        }

        .import-row {
          display: flex;
          gap: 10px;
          align-items: center;
        }

        .file-name {
          color: #606266;
          font-size: 14px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 250px;

          &.placeholder {
            color: #c0c4cc;
          }
        }
      }
    }
  }
  
  .backups-card {
    .card-header {
      span {
        font-size: 18px;
        font-weight: bold;
      }
    }
  }
}
</style>
