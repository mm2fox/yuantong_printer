import api from './auth'

export const printerTemplateApi = {
  getList: (templateType) => api.get('/printer-templates', { params: { template_type: templateType } }),
  getById: (id) => api.get(`/printer-templates/${id}`),
  create: (data) => api.post('/printer-templates', data),
  update: (id, data) => api.put(`/printer-templates/${id}`, data),
  delete: (id) => api.delete(`/printer-templates/${id}`),
  setDefault: (id) => api.put(`/printer-templates/${id}/set-default`),
  uploadImage: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/printer-templates/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  silentPrint: (data) => api.post('/silent-print', data),
  generatePdf: (data) => api.post('/silent-print/generate-pdf', data, { responseType: 'blob' }),
  generatePdfFromConfig: (data) => api.post('/silent-print/generate-pdf-from-config', data, { responseType: 'blob' }),
  rotateImage: (data) => api.post('/printer-templates/rotate-image', data)
}
