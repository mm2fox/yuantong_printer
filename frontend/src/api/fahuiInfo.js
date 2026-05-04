import api from './auth'

export const fahuiInfoApi = {
  getList: (keyword) => api.get('/fahui-info', { params: { keyword } }),
  getById: (id) => api.get(`/fahui-info/${id}`),
  create: (data) => api.post('/fahui-info', data),
  update: (id, data) => api.put(`/fahui-info/${id}`, data),
  delete: (id) => api.delete(`/fahui-info/${id}`)
}
