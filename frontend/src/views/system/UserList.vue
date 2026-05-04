<template>
  <div class="user-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="handleAdd">新增用户</el-button>
        </div>
      </template>
      
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名/真实姓名"
          style="width: 200px"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-select v-model="searchRole" placeholder="角色" clearable style="width: 120px; margin-left: 10px" @change="handleSearch">
          <el-option label="管理员" value="管理员" />
          <el-option label="普通用户" value="普通用户" />
        </el-select>
        <el-button type="primary" style="margin-left: 10px" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>
      
      <el-table :data="filteredData" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="真实姓名" width="120" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === '管理员' ? 'danger' : 'info'">
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="temple_name" label="所属寺庙" width="120">
          <template #default="{ row }">
            {{ row.temple_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="warning" link @click="handlePermissions(row)" :disabled="row.role === '管理员'">权限</el-button>
            <el-button type="info" link @click="handleResetPassword(row)">重置密码</el-button>
            <el-button type="danger" link @click="handleDelete(row)" :disabled="row.username === 'admin'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" :disabled="isEdit" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="formData.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="密码" :prop="isEdit ? '' : 'password'">
          <el-input v-model="formData.password" type="password" show-password :placeholder="isEdit ? '留空则不修改' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" style="width: 100%">
            <el-option label="管理员" value="管理员" />
            <el-option label="普通用户" value="普通用户" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属寺庙">
          <el-select v-model="formData.temple_id" placeholder="请选择寺庙" clearable style="width: 100%">
            <el-option v-for="temple in templeList" :key="temple.id" :label="temple.寺庙名称" :value="temple.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="formData.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="permissionDialogVisible"
      title="权限管理"
      width="500px"
      destroy-on-close
    >
      <div class="permission-header">
        <span>用户: {{ currentUser.real_name }} ({{ currentUser.username }})</span>
      </div>
      
      <el-checkbox-group v-model="selectedPermissions" class="permission-group">
        <el-checkbox 
          v-for="perm in allPermissions" 
          :key="perm.name" 
          :label="perm.name"
          class="permission-item"
        >
          {{ perm.display_name }}
          <span class="permission-desc">{{ perm.description }}</span>
        </el-checkbox>
      </el-checkbox-group>
      
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSavePermissions" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="resetPasswordVisible"
      title="重置密码"
      width="400px"
      destroy-on-close
    >
      <el-form :model="resetPasswordForm" label-width="80px">
        <el-form-item label="用户">
          <span>{{ resetPasswordForm.real_name }} ({{ resetPasswordForm.username }})</span>
        </el-form-item>
        <el-form-item label="新密码" prop="password">
          <el-input v-model="resetPasswordForm.password" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="resetPasswordVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmResetPassword" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authApi } from '@/api/auth'
import { permissionApi } from '@/api/permissions'
import { templeApi } from '@/api/temples'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const templeList = ref([])
const dialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const resetPasswordVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const searchKeyword = ref('')
const searchRole = ref('')

const currentUser = ref({})
const allPermissions = ref([])
const selectedPermissions = ref([])

const formData = reactive({
  id: null,
  username: '',
  real_name: '',
  password: '',
  role: '普通用户',
  temple_id: null,
  is_active: true
})

const resetPasswordForm = reactive({
  id: null,
  username: '',
  real_name: '',
  password: ''
})

const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const filteredData = computed(() => {
  let data = tableData.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    data = data.filter(item => 
      item.username?.toLowerCase().includes(keyword) ||
      item.real_name?.toLowerCase().includes(keyword)
    )
  }
  if (searchRole.value) {
    data = data.filter(item => item.role === searchRole.value)
  }
  return data
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return dateStr.replace('T', ' ').substring(0, 19)
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await authApi.getUsers()
    tableData.value = res
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchTemples = async () => {
  try {
    const res = await templeApi.getList()
    templeList.value = res
  } catch (error) {
    console.error('获取寺庙列表失败:', error)
  }
}

const fetchPermissions = async () => {
  try {
    const res = await permissionApi.getList()
    allPermissions.value = res
  } catch (error) {
    console.error('获取权限列表失败:', error)
  }
}

const handleSearch = () => {
  // 搜索通过computed自动处理
}

const handleReset = () => {
  searchKeyword.value = ''
  searchRole.value = ''
}

const resetForm = () => {
  Object.assign(formData, {
    id: null,
    username: '',
    real_name: '',
    password: '',
    role: '普通用户',
    temple_id: null,
    is_active: true
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
    username: row.username,
    real_name: row.real_name,
    password: '',
    role: row.role,
    temple_id: row.temple_id,
    is_active: row.is_active
  })
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该用户吗？', '提示', {
      type: 'warning'
    })
    await authApi.deleteUser(row.id)
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
          await authApi.updateUser(formData.id, formData)
          ElMessage.success('更新成功')
        } else {
          await authApi.createUser(formData)
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

const handlePermissions = async (row) => {
  currentUser.value = row
  
  try {
    const res = await permissionApi.getUserPermissions(row.id)
    selectedPermissions.value = res.permissions || []
  } catch (error) {
    console.error('获取用户权限失败:', error)
    selectedPermissions.value = []
  }
  
  if (allPermissions.value.length === 0) {
    await fetchPermissions()
  }
  
  permissionDialogVisible.value = true
}

const handleSavePermissions = async () => {
  submitLoading.value = true
  try {
    await permissionApi.updateUserPermissions(currentUser.value.id, selectedPermissions.value)
    ElMessage.success('权限保存成功')
    permissionDialogVisible.value = false
  } catch (error) {
    console.error('保存权限失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const handleResetPassword = (row) => {
  Object.assign(resetPasswordForm, {
    id: row.id,
    username: row.username,
    real_name: row.real_name,
    password: ''
  })
  resetPasswordVisible.value = true
}

const handleConfirmResetPassword = async () => {
  if (!resetPasswordForm.password) {
    ElMessage.warning('请输入新密码')
    return
  }
  
  submitLoading.value = true
  try {
    await authApi.updateUser(resetPasswordForm.id, { password: resetPasswordForm.password })
    ElMessage.success('密码重置成功')
    resetPasswordVisible.value = false
  } catch (error) {
    console.error('密码重置失败:', error)
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchTemples()
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

.permission-header {
  margin-bottom: 20px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.permission-group {
  display: flex;
  flex-direction: column;
}

.permission-item {
  margin: 10px 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.permission-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  margin-left: 24px;
}
</style>
