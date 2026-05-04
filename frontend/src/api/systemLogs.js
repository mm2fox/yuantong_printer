import api from './auth'

export const systemLogApi = {
  getList: (params) => api.get('/system-logs', { params }),
  getCount: (params) => api.get('/system-logs/count', { params }),
  create: (data) => api.post('/system-logs', data),
  delete: (data) => api.delete('/system-logs', { data }),
  getMyLogs: (params) => api.get('/system-logs/my-logs', { params }),
  getMyLogCount: (params) => api.get('/system-logs/my-logs/count', { params })
}
