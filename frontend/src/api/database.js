import api from './auth'

export const databaseApi = {
  getInfo() {
    return api.get('/database/info')
  },

  backup() {
    return api.post('/database/backup')
  },

  getBackups() {
    return api.get('/database/backups')
  },

  restore(backupFilename) {
    return api.post(`/database/restore/${backupFilename}`)
  },

  deleteBackup(backupFilename) {
    return api.delete(`/database/backups/${backupFilename}`)
  },

  clear() {
    return api.post('/database/clear')
  },

  getClearableTables() {
    return api.get('/database/clearable-tables')
  },

  clearTable(tableName) {
    return api.post(`/database/clear-table/${tableName}`)
  },

  init() {
    return api.post('/database/init')
  },

  downloadBackup(backupFilename) {
    return `/api/database/download/${backupFilename}`
  },

  previewExcel(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/database/excel-preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
  },

  importExcel(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/database/import-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000
    })
  },

  cleanupImages() {
    return api.post('/printer-templates/cleanup-images')
  }
}
