import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import Login from '@/views/Login.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/query/fahui'
      },
      {
        path: 'query/fahui',
        name: 'FahuiQuery',
        component: () => import('@/views/query/FahuiQuery.vue'),
        meta: { title: '法会记录查询' }
      },
      {
        path: 'query/shizhu',
        name: 'ShizhuQuery',
        component: () => import('@/views/query/ShizhuQuery.vue'),
        meta: { title: '施主查询' }
      },
      {
        path: 'query/register',
        name: 'FahuiRegister',
        component: () => import('@/views/fahui/FahuiRecordList.vue'),
        meta: { title: '法会登记' }
      },
      {
        path: 'shizhu',
        name: 'ShizhuList',
        component: () => import('@/views/shizhu/ShizhuList.vue'),
        meta: { title: '施主信息' }
      },
      {
        path: 'fahui',
        name: 'FahuiList',
        component: () => import('@/views/fahui/FahuiList.vue'),
        meta: { title: '所有法会' }
      },
      {
        path: 'print',
        name: 'PrintList',
        component: () => import('@/views/print/PrintList.vue'),
        meta: { title: '所有打印' }
      },
      {
        path: 'print/templates',
        name: 'TemplateList',
        component: () => import('@/views/print/TemplateList.vue'),
        meta: { title: '打印模板', requiredPermission: 'print_template' }
      },
      {
        path: 'system/users',
        name: 'UserList',
        component: () => import('@/views/system/UserList.vue'),
        meta: { title: '用户管理', requiresAdmin: true }
      },
      {
        path: 'system/temples',
        name: 'TempleList',
        component: () => import('@/views/system/TempleList.vue'),
        meta: { title: '寺庙管理', requiresAdmin: true }
      },
      {
        path: 'system/logs',
        name: 'SystemLog',
        component: () => import('@/views/system/SystemLog.vue'),
        meta: { title: '系统日志', requiresAdmin: true }
      },
      {
        path: 'system/database',
        name: 'DatabaseManagement',
        component: () => import('@/views/system/DatabaseManagement.vue'),
        meta: { title: '数据库管理', requiresAdmin: true }
      },
      {
        path: 'system/version',
        name: 'VersionInfo',
        component: () => import('@/views/system/VersionInfo.vue'),
        meta: { title: '版本信息', requiresAdmin: true }
      },
      {
        path: 'system/user-data',
        name: 'UserData',
        component: () => import('@/views/system/UserData.vue'),
        meta: { title: '用户数据' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth !== false && !userStore.isLoggedIn()) {
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn()) {
    next('/query/fahui')
  } else if (to.meta.requiresAdmin && userStore.userInfo?.role !== '管理员') {
    next('/query/fahui')
  } else if (to.meta.requiredPermission && !userStore.hasPermission(to.meta.requiredPermission)) {
    next('/query/fahui')
  } else {
    next()
  }
})

export default router
