import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))

  const login = async (loginForm) => {
    const res = await authApi.login(loginForm)
    token.value = res.access_token
    userInfo.value = res.user
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('userInfo', JSON.stringify(res.user))
    return res
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      token.value = ''
      userInfo.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
    }
  }

  const getUserInfo = async () => {
    const res = await authApi.getMe()
    userInfo.value = res
    localStorage.setItem('userInfo', JSON.stringify(res))
    return res
  }

  const isLoggedIn = () => {
    return !!token.value
  }

  const isAdmin = () => {
    return userInfo.value?.role === '管理员'
  }

  return {
    token,
    userInfo,
    login,
    logout,
    getUserInfo,
    isLoggedIn,
    isAdmin
  }
})
