import api from './auth'

export const fahuiUserApi = {
  getList: (keyword, limit) => api.get('/fahui-users', { params: { keyword, limit } }),
  getById: (id) => api.get(`/fahui-users/${id}`),
  create: (data) => api.post('/fahui-users', data),
  update: (id, data) => api.put(`/fahui-users/${id}`, data),
  delete: (id) => api.delete(`/fahui-users/${id}`),
  generateCode: () => api.get('/fahui-users/generate-code')
}
