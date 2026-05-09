import api from './auth'

export const versionInfoApi = {
  getList: () => api.get('/version-info'),
  getLatest: () => api.get('/version-info/latest'),
  getCount: () => api.get('/version-info/count'),
  create: (data) => api.post('/version-info', data),
  importBuildInfo: () => api.post('/version-info/import-build-info'),
  delete: (id) => api.delete(`/version-info/${id}`)
}
