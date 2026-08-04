<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2 @click="handleTitleClick">缘通寺院信息管理系统</h2>
        </div>
      </template>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-select
            v-model="loginForm.username"
            placeholder="请选择用户"
            size="large"
            style="width: 100%"
            :loading="usersLoading"
          >
            <el-option
              v-for="user in filteredUserList"
              :key="user"
              :label="user"
              :value="user"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-button"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getUserList } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const loading = ref(false)
const usersLoading = ref(false)
const userList = ref([])
const showAdmin = ref(false)
const clickCount = ref(0)
const clickTimer = ref(null)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请选择用户', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const filteredUserList = computed(() => {
  if (showAdmin.value) return userList.value
  return userList.value.filter(user => user !== 'admin')
})

const handleTitleClick = () => {
  clickCount.value++

  if (clickCount.value === 1) {
    clickTimer.value = setTimeout(() => {
      if (clickCount.value === 6) {
        showAdmin.value = !showAdmin.value
        if (showAdmin.value) {
          ElMessage.success('已显示管理员用户')
        } else {
          ElMessage.info('已隐藏管理员用户')
        }
      }
      clickCount.value = 0
    }, 1000)
  }

  if (clickCount.value > 6) {
    clickCount.value = 0
    if (clickTimer.value) {
      clearTimeout(clickTimer.value)
    }
  }
}

const fetchUserList = async () => {
  usersLoading.value = true
  try {
    const response = await getUserList()
    userList.value = response
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.login(loginForm)
        ElMessage.success('登录成功')
        router.push('/query/fahui')
      } catch (error) {
        console.error('登录失败:', error)
        ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }
  })
}

onMounted(() => {
  fetchUserList()
})
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  
  .card-header {
    text-align: center;
    
    h2 {
      margin: 0;
      color: #303133;
      cursor: pointer;
      user-select: none;
    }
  }
}

.login-form {
  padding: 20px 0;
  
  .login-button {
    width: 100%;
  }
}
</style>
