import api from './auth'

export const scannerApi = {
  getDevices: () => api.get('/scanner/devices'),
  scan: (data) => api.post('/scanner/scan', data, { timeout: 120000 })
}
