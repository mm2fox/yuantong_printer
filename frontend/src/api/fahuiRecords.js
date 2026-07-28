import api from './auth'

export const fahuiRecordApi = {
  getList: (fahuiName) => api.get('/fahui-records', { params: { fahui_name: fahuiName } }),
  getById: (id) => api.get(`/fahui-records/${id}`),
  create: (data) => api.post('/fahui-records', data),
  batchCreate: (data) => api.post('/fahui-records/batch', data),
  update: (id, data) => api.put(`/fahui-records/${id}`, data),
  delete: (id) => api.delete(`/fahui-records/${id}`),
  queryByFahui: (params) => api.get('/fahui-records/query-by-fahui', { params }),
  queryByShizhu: (params) => api.get('/fahui-records/query-by-shizhu', { params })
}
