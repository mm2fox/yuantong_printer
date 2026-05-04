import api from './auth'

export const permissionApi = {
  getList: () => api.get('/permissions'),
  getUserPermissions: (userId) => api.get(`/permissions/user/${userId}`),
  updateUserPermissions: (userId, permissions) => api.put(`/permissions/user/${userId}`, { permissions })
}
