<template>
  <div class="layout-container">
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <h1>缘通寺院信息管理系统</h1>
        </div>
        <div class="header-right">
          <span class="user-info">当前用户: {{ userStore.userInfo?.real_name || userStore.userInfo?.username }}</span>
          <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      
      <el-container>
        <el-aside width="200px" class="layout-aside">
          <el-menu
            :default-active="activeMenu"
            router
            class="layout-menu"
          >
            <el-sub-menu index="query">
              <template #title>
                <el-icon><Search /></el-icon>
                <span>查询</span>
              </template>
              <el-menu-item index="/query/fahui">法会记录查询</el-menu-item>
              <el-menu-item index="/query/shizhu">施主查询</el-menu-item>
            </el-sub-menu>
            
            <el-menu-item index="/query/register">
              <el-icon><Edit /></el-icon>
              <span>法会登记</span>
            </el-menu-item>
            
            <el-menu-item index="/shizhu">
              <el-icon><User /></el-icon>
              <span>施主管理</span>
            </el-menu-item>
            
            <el-menu-item index="/fahui">
              <el-icon><Calendar /></el-icon>
              <span>法会管理</span>
            </el-menu-item>
            
            <el-sub-menu index="print">
              <template #title>
                <el-icon><Printer /></el-icon>
                <span>打印管理</span>
              </template>
              <el-menu-item index="/print">所有打印</el-menu-item>
              <el-menu-item index="/print/templates" v-if="canManageTemplates">打印模板</el-menu-item>
            </el-sub-menu>
            
            <el-menu-item index="/system/user-data">
              <el-icon><Document /></el-icon>
              <span>用户数据</span>
            </el-menu-item>
            
            <el-sub-menu index="system" v-if="isAdmin">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>系统管理</span>
              </template>
              <el-menu-item index="/system/users">用户管理</el-menu-item>
              <el-menu-item index="/system/temples">寺庙管理</el-menu-item>
              <el-menu-item index="/system/logs">系统日志</el-menu-item>
              <el-menu-item index="/system/database">数据库管理</el-menu-item>
            </el-sub-menu>
          </el-menu>
        </el-aside>
        
        <el-main class="layout-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Calendar, Printer, User, Search, Setting, Edit, Document } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => {
  return route.path
})

const isAdmin = computed(() => {
  return userStore.userInfo?.role === '管理员'
})

const canManageTemplates = computed(() => {
  return userStore.hasPermission('print_template')
})

const handleLogout = async () => {
  await userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: 100vh;
}

.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  padding: 0 20px;
}

.header-left h1 {
  font-size: 20px;
  color: #fff;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-info {
  color: #fff;
  font-size: 14px;
}

.layout-aside {
  background: #fff;
  border-right: 1px solid #e6e6e6;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

.layout-menu {
  border-right: none;
  height: 100%;
}

.layout-main {
  background: #f5f7fa;
  padding: 20px;
  min-height: calc(100vh - 60px);
}
</style>
