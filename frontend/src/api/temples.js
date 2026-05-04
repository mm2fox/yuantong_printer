import api from './auth'

export const templeApi = {
  getList: () => api.get('/temples'),
  create: (data) => api.post('/temples', data),
  update: (id, data) => api.put(`/temples/${id}`, data),
  delete: (id) => api.delete(`/temples/${id}`)
}
