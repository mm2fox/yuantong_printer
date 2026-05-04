<template>
  <div class="temple-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>寺庙管理</span>
          <el-button type="primary" @click="handleAdd">新增寺庙</el-button>
        </div>
      </template>
      
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索寺庙名称/地址"
          style="width: 250px"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" style="margin-left: 10px" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>
      
      <el-table :data="filteredData" v-loading="loading" stripe>
        <el-table-column prop="寺庙名称" label="寺庙名称" width="150" />
        <el-table-column prop="寺庙地址" label="寺庙地址" min-width="200" />
        <el-table-column prop="联系电话" label="联系电话" width="130" />
        <el-table-column prop="user_count" label="用户数量" width="100">
          <template #default="{ row }">
            <el-tag type="info">{{ row.user_count || 0 }} 人</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="备注" label="备注" min-width="150">
          <template #default="{ row }">
            {{ row.备注 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)" :disabled="row.user_count > 0">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="statistics">
        <span>共 {{ filteredData.length }} 个寺庙</span>
        <span style="margin-left: 20px">总用户数: {{ totalUsers }} 人</span>
      </div>
    </el-card>
    
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑寺庙' : '新增寺庙'"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="寺庙名称" prop="寺庙名称">
          <el-input v-model="formData.寺庙名称" placeholder="请输入寺庙名称" />
        </el-form-item>
        <el-form-item label="寺庙地址">
          <el-input v-model="formData.寺庙地址" placeholder="请输入寺庙地址" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="formData.联系电话" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.备注" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { templeApi } from '@/api/temples'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const searchKeyword = ref('')

const formData = reactive({
  id: null,
  寺庙名称: '',
  寺庙地址: '',
  联系电话: '',
  备注: ''
})

const formRules = {
  寺庙名称: [{ required: true, message: '请输入寺庙名称', trigger: 'blur' }]
}

const filteredData = computed(() => {
  if (!searchKeyword.value) return tableData.value
  const keyword = searchKeyword.value.toLowerCase()
  return tableData.value.filter(item => 
    item.寺庙名称?.toLowerCase().includes(keyword) ||
    item.寺庙地址?.toLowerCase().includes(keyword)
  )
})

const totalUsers = computed(() => {
  return tableData.value.reduce((sum, item) => sum + (item.user_count || 0), 0)
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return dateStr.replace('T', ' ').substring(0, 19)
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await templeApi.getList()
    tableData.value = res
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 搜索通过computed自动处理
}

const handleReset = () => {
  searchKeyword.value = ''
}

const resetForm = () => {
  Object.assign(formData, {
    id: null,
    寺庙名称: '',
    寺庙地址: '',
    联系电话: '',
    备注: ''
  })
}

const handleAdd = () => {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

const handleEdit = (row) => {
  resetForm()
  isEdit.value = true
  Object.assign(formData, {
    id: row.id,
    寺庙名称: row.寺庙名称,
    寺庙地址: row.寺庙地址,
    联系电话: row.联系电话,
    备注: row.备注
  })
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  if (row.user_count > 0) {
    ElMessage.warning('该寺庙下有用户，无法删除')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要删除该寺庙吗？', '提示', {
      type: 'warning'
    })
    await templeApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEdit.value) {
          await templeApi.update(formData.id, formData)
          ElMessage.success('更新成功')
        } else {
          await templeApi.create(formData)
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
